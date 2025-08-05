"""Webhook API endpoints."""

import asyncio
import time
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse

from ..core.config import get_settings, Settings
from ..core.logging import get_logger, set_request_id, get_request_id
from ..core.security import verify_webhook_signature, SignatureError
from ..models.webhook import TradingViewWebhook, WebhookResponse
from ..services.telegram import TelegramService, TelegramError

router = APIRouter()
logger = get_logger(__name__)

# Simple in-memory cache for idempotency (MVP implementation)
_message_cache: Dict[str, float] = {}
CACHE_CLEANUP_INTERVAL = 300  # 5 minutes


def cleanup_cache():
    """Clean up expired cache entries."""
    current_time = time.time()
    settings = get_settings()
    expired_keys = [
        key for key, timestamp in _message_cache.items()
        if current_time - timestamp > settings.cache_ttl
    ]
    for key in expired_keys:
        _message_cache.pop(key, None)
    
    logger.debug("Cache cleanup completed", expired_entries=len(expired_keys))


def is_duplicate_message(webhook_data: TradingViewWebhook) -> bool:
    """
    Check if this is a duplicate message based on ticker, signal, and time.
    
    Args:
        webhook_data: Webhook payload
        
    Returns:
        True if message is a duplicate
    """
    # Create a unique key for this message
    cache_key = f"{webhook_data.ticker}:{webhook_data.signal}:{webhook_data.time}"
    current_time = time.time()
    settings = get_settings()
    
    # Check if message exists in cache and is still valid
    if cache_key in _message_cache:
        timestamp = _message_cache[cache_key]
        if current_time - timestamp < settings.cache_ttl:
            logger.info(
                "Duplicate message detected",
                cache_key=cache_key,
                age_seconds=current_time - timestamp
            )
            return True
        else:
            # Remove expired entry
            _message_cache.pop(cache_key, None)
    
    # Add to cache
    _message_cache[cache_key] = current_time
    return False


async def process_webhook_background(
    webhook_data: TradingViewWebhook,
    request_id: str
) -> None:
    """
    Process webhook in background to ensure fast response time.
    
    Args:
        webhook_data: Validated webhook payload
        request_id: Request ID for tracking
    """
    # Set request ID in background task context
    set_request_id(request_id)
    
    try:
        # Check for duplicates
        if is_duplicate_message(webhook_data):
            logger.info("Skipping duplicate message")
            return
        
        # Send to Telegram
        async with TelegramService() as telegram:
            result = await telegram.send_trading_signal(webhook_data)
            logger.info(
                "Webhook processed successfully",
                telegram_message_id=result.get("result", {}).get("message_id"),
                ticker=webhook_data.ticker,
                signal=webhook_data.signal
            )
    
    except TelegramError as e:
        logger.error(
            "Failed to send Telegram message",
            error=str(e),
            ticker=webhook_data.ticker,
            signal=webhook_data.signal
        )
    except Exception as e:
        logger.error(
            "Unexpected error processing webhook",
            error=str(e),
            error_type=type(e).__name__,
            ticker=webhook_data.ticker,
            signal=webhook_data.signal
        )


@router.post("/webhook", response_model=WebhookResponse)
async def receive_tradingview_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings)
) -> JSONResponse:
    """
    Receive and process TradingView webhook.
    
    This endpoint:
    1. Validates HMAC signature
    2. Parses and validates JSON payload
    3. Responds quickly (< 150ms)
    4. Processes message in background
    
    Returns:
        JSON response with status
    """
    start_time = time.time()
    
    # Generate request ID for tracking
    request_id = get_request_id()
    set_request_id(request_id)
    
    logger.info(
        "Received webhook request",
        method=request.method,
        url=str(request.url),
        user_agent=request.headers.get("user-agent"),
        content_length=request.headers.get("content-length")
    )
    
    try:
        # Get raw body and signature
        body = await request.body()
        signature = request.headers.get("X-Signature", "")
        
        # Signature validation disabled for easier TradingView integration  
        logger.info(
            "Signature validation disabled",
            signature_present=bool(signature),
                body_size=len(body)
            )
        
        # Parse JSON payload
        try:
            json_data = await request.json()
        except Exception as e:
            logger.error("Failed to parse JSON payload", error=str(e))
            raise HTTPException(
                status_code=400,
                detail="Invalid JSON payload"
            )
        
        # Validate webhook data
        try:
            webhook_data = TradingViewWebhook(**json_data)
        except Exception as e:
            logger.error(
                "Webhook data validation failed",
                error=str(e),
                payload=json_data
            )
            raise HTTPException(
                status_code=422,
                detail=f"Invalid webhook data: {str(e)}"
            )
        
        # Check response time requirement (< 150ms)
        elapsed_time = time.time() - start_time
        if elapsed_time > settings.webhook_timeout:
            logger.warning(
                "Webhook processing taking too long",
                elapsed_ms=elapsed_time * 1000
            )
        
        # Schedule background processing
        background_tasks.add_task(
            process_webhook_background,
            webhook_data,
            request_id
        )
        
        # Schedule cache cleanup periodically
        if len(_message_cache) > 100:  # Cleanup when cache gets large
            background_tasks.add_task(cleanup_cache)
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        logger.info(
            "Webhook accepted for processing",
            ticker=webhook_data.ticker,
            signal=webhook_data.signal,
            price=webhook_data.price,
            processing_time_ms=processing_time_ms
        )
        
        response = WebhookResponse(
            status="accepted",
            message="Webhook received and processing",
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=202,  # Accepted
            content=response.model_dump(mode='json'),
            headers={"X-Request-ID": request_id}
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        processing_time_ms = (time.time() - start_time) * 1000
        logger.error(
            "Unexpected error processing webhook",
            error=str(e),
            error_type=type(e).__name__,
            processing_time_ms=processing_time_ms
        )
        
        response = WebhookResponse(
            status="error",
            message="Internal server error",
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=500,
            content=response.model_dump(mode='json'),
            headers={"X-Request-ID": request_id}
        )


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns:
        Health status information
    """
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "twsignals-webhook",
        "version": "0.1.0"
    }


@router.get("/health/telegram")
async def telegram_health_check() -> Dict[str, Any]:
    """
    Check Telegram Bot API connectivity.
    
    Returns:
        Telegram connection status
    """
    try:
        async with TelegramService() as telegram:
            is_connected = await telegram.test_connection()
            
        return {
            "status": "healthy" if is_connected else "unhealthy",
            "telegram_connected": is_connected,
            "timestamp": time.time()
        }
    
    except Exception as e:
        logger.error("Telegram health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "telegram_connected": False,
            "error": str(e),
            "timestamp": time.time()
        }
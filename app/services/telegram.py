"""Telegram Bot API service with retry logic and rate limiting."""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

import httpx
from pydantic import ValidationError

from ..core.config import get_settings
from ..core.logging import get_logger
from ..models.webhook import TradingViewWebhook, TelegramMessage

logger = get_logger(__name__)


class TelegramError(Exception):
    """Base exception for Telegram API errors."""
    pass


class TelegramRateLimitError(TelegramError):
    """Raised when rate limit is exceeded."""
    pass


class TelegramService:
    """Service for sending messages to Telegram via Bot API."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = httpx.AsyncClient(
            timeout=self.settings.tg_timeout,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        self._last_request_time: Optional[datetime] = None
        self._request_count = 0
        self._rate_limit_reset_time: Optional[datetime] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    def _format_message(self, webhook_data: TradingViewWebhook) -> str:
        """
        Format TradingView webhook data into a Telegram message.
        
        Args:
            webhook_data: Webhook payload from TradingView
            
        Returns:
            Formatted message string
        """
        # Base message format as per requirements
        message_lines = [
            f"<b>{webhook_data.ticker}</b>",
            f"Signal: <i>{webhook_data.signal}</i>  Price: {webhook_data.price}"
        ]
        
        # Add interval if provided
        if webhook_data.interval:
            message_lines[0] += f"  ({webhook_data.interval})"
        
        # Add timestamp
        message_lines.append(f"🕒 {webhook_data.time}")
        
        # Add chart link if provided
        if webhook_data.chart:
            message_lines.append(f"📈 <a href='{webhook_data.chart}'>Chart</a>")
        
        return "\n".join(message_lines)
    
    async def _check_rate_limit(self) -> None:
        """Check and enforce rate limiting (30 messages per second)."""
        now = datetime.utcnow()
        
        # Reset counter every second
        if (self._rate_limit_reset_time is None or 
            now >= self._rate_limit_reset_time):
            self._request_count = 0
            self._rate_limit_reset_time = now + timedelta(seconds=1)
        
        # Check if we've exceeded the rate limit
        if self._request_count >= 30:
            sleep_time = (self._rate_limit_reset_time - now).total_seconds()
            if sleep_time > 0:
                logger.warning(
                    "Rate limit exceeded, sleeping",
                    sleep_time=sleep_time,
                    request_count=self._request_count
                )
                await asyncio.sleep(sleep_time)
                self._request_count = 0
                self._rate_limit_reset_time = datetime.utcnow() + timedelta(seconds=1)
        
        self._request_count += 1
    
    async def _send_message_with_retry(
        self, 
        message: TelegramMessage
    ) -> Dict[str, Any]:
        """
        Send message to Telegram with retry logic.
        
        Args:
            message: Telegram message to send
            
        Returns:
            API response data
            
        Raises:
            TelegramError: If all retry attempts fail
        """
        url = f"{self.settings.telegram_base_url}/sendMessage"
        
        for attempt in range(self.settings.tg_retry_attempts):
            try:
                await self._check_rate_limit()
                
                logger.debug(
                    "Sending Telegram message",
                    attempt=attempt + 1,
                    chat_id=message.chat_id,
                    text_length=len(message.text)
                )
                
                response = await self.client.post(
                    url,
                    json=message.model_dump(),
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        logger.info(
                            "Message sent successfully",
                            message_id=result.get("result", {}).get("message_id"),
                            chat_id=message.chat_id
                        )
                        return result
                    else:
                        error_msg = result.get("description", "Unknown error")
                        logger.error(
                            "Telegram API returned error",
                            error_code=result.get("error_code"),
                            description=error_msg
                        )
                        raise TelegramError(f"API error: {error_msg}")
                
                elif response.status_code == 429:
                    # Rate limited
                    retry_after = int(response.headers.get("Retry-After", 1))
                    logger.warning(
                        "Rate limited by Telegram",
                        retry_after=retry_after,
                        attempt=attempt + 1
                    )
                    if attempt < self.settings.tg_retry_attempts - 1:
                        await asyncio.sleep(retry_after)
                        continue
                    raise TelegramRateLimitError(f"Rate limited, retry after {retry_after}s")
                
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.error(
                        "HTTP error from Telegram API",
                        status_code=response.status_code,
                        response_text=response.text[:500]
                    )
                    raise TelegramError(error_msg)
                    
            except httpx.TimeoutException as e:
                logger.warning(
                    "Timeout sending message",
                    attempt=attempt + 1,
                    error=str(e)
                )
                if attempt == self.settings.tg_retry_attempts - 1:
                    raise TelegramError(f"Timeout after {self.settings.tg_retry_attempts} attempts")
                
            except httpx.RequestError as e:
                logger.warning(
                    "Request error sending message",
                    attempt=attempt + 1,
                    error=str(e)
                )
                if attempt == self.settings.tg_retry_attempts - 1:
                    raise TelegramError(f"Request error: {str(e)}")
            
            except TelegramError:
                # Re-raise Telegram-specific errors
                raise
            
            except Exception as e:
                logger.error(
                    "Unexpected error sending message",
                    attempt=attempt + 1,
                    error=str(e),
                    error_type=type(e).__name__
                )
                if attempt == self.settings.tg_retry_attempts - 1:
                    raise TelegramError(f"Unexpected error: {str(e)}")
            
            # Calculate delay for next retry
            if attempt < self.settings.tg_retry_attempts - 1:
                delay = self.settings.tg_retry_delay * (
                    self.settings.tg_retry_backoff ** attempt
                )
                logger.info(f"Retrying in {delay}s", attempt=attempt + 1)
                await asyncio.sleep(delay)
        
        raise TelegramError(f"Failed after {self.settings.tg_retry_attempts} attempts")
    
    async def send_trading_signal(self, webhook_data: TradingViewWebhook) -> Dict[str, Any]:
        """
        Send a trading signal message to Telegram.
        
        Args:
            webhook_data: TradingView webhook payload
            
        Returns:
            Telegram API response
            
        Raises:
            TelegramError: If message sending fails
            ValidationError: If message data is invalid
        """
        try:
            # Format the message
            message_text = self._format_message(webhook_data)
            
            # Create Telegram message
            message = TelegramMessage(
                chat_id=self.settings.tg_chat_id,
                text=message_text,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            
            logger.info(
                "Sending trading signal",
                ticker=webhook_data.ticker,
                signal=webhook_data.signal,
                price=webhook_data.price,
                chat_id=self.settings.tg_chat_id
            )
            
            # Send with retry logic
            result = await self._send_message_with_retry(message)
            
            return result
            
        except ValidationError as e:
            logger.error("Invalid message data", validation_errors=e.errors())
            raise TelegramError(f"Message validation failed: {str(e)}")
        except Exception as e:
            logger.error(
                "Error sending trading signal",
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    async def test_connection(self) -> bool:
        """
        Test connection to Telegram Bot API.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            url = f"{self.settings.telegram_base_url}/getMe"
            response = await self.client.get(url)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    bot_info = result.get("result", {})
                    logger.info(
                        "Telegram connection test successful",
                        bot_username=bot_info.get("username"),
                        bot_id=bot_info.get("id")
                    )
                    return True
            
            logger.error(
                "Telegram connection test failed",
                status_code=response.status_code,
                response=response.text
            )
            return False
            
        except Exception as e:
            logger.error("Error testing Telegram connection", error=str(e))
            return False
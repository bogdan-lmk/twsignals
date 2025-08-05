"""FastAPI application for TradingView to Telegram webhook service."""

import time
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.webhook import router as webhook_router
from .core.config import get_settings
from .core.logging import setup_logging, get_logger, set_request_id


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger = get_logger(__name__)
    settings = get_settings()
    
    logger.info(
        "Starting TradingView Telegram Webhook Service",
        version="0.1.0",
        debug=settings.debug,
        log_level=settings.log_level
    )
    
    # Test Telegram connection on startup
    try:
        from .services.telegram import TelegramService
        async with TelegramService() as telegram:
            connection_ok = await telegram.test_connection()
            if not connection_ok:
                logger.warning("Telegram connection test failed during startup")
            else:
                logger.info("Telegram connection verified during startup")
    except Exception as e:
        logger.error("Failed to test Telegram connection during startup", error=str(e))
    
    yield
    
    # Shutdown
    logger.info("Shutting down TradingView Telegram Webhook Service")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    # Setup logging first
    setup_logging()
    logger = get_logger(__name__)
    settings = get_settings()
    
    # Create FastAPI app
    app = FastAPI(
        title="TradingView Telegram Webhook",
        description="Fast webhook service for forwarding TradingView alerts to Telegram",
        version="0.1.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_hosts,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    
    @app.middleware("http")
    async def request_middleware(request: Request, call_next):
        """Add request ID and timing middleware."""
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        set_request_id(request_id)
        
        # Track request timing
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Add timing and request ID to response
        process_time = time.time() - start_time
        
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log request completion
        logger.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time_ms=process_time * 1000,
            request_id=request_id
        )
        
        return response
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Global exception handler."""
        request_id = request.headers.get("X-Request-ID", "unknown")
        
        logger.error(
            "Unhandled exception",
            error=str(exc),
            error_type=type(exc).__name__,
            method=request.method,
            url=str(request.url),
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Internal server error",
                "request_id": request_id
            },
            headers={"X-Request-ID": request_id}
        )
    
    # Include routers
    app.include_router(webhook_router, tags=["webhook"])
    
    # Root endpoint
    @app.get("/", tags=["root"])
    async def root() -> Dict[str, Any]:
        """Root endpoint with service information."""
        return {
            "service": "TradingView Telegram Webhook",
            "version": "0.1.0",
            "status": "running",
            "timestamp": time.time(),
            "docs_url": "/docs" if settings.debug else None
        }
    
    return app


# Create app instance
app = create_app()
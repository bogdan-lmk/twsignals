#!/usr/bin/env python3
"""
TradingView to Telegram Webhook Service - Main Entry Point

This is the main entry point for the FastAPI-based webhook service.
The original Flask implementation has been replaced with a more robust
FastAPI application with proper error handling, logging, and retry logic.

Usage:
    python main.py                    # Development server
    uvicorn main:app --reload         # Development with auto-reload
    uvicorn main:app --host 0.0.0.0 --port 8000  # Production
"""

import uvicorn
from app.main import app
from app.core.config import get_settings


def main():
    """Run the application with uvicorn."""
    settings = get_settings()
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True,
        server_header=False,  # Security: don't expose server info
        date_header=False,    # Security: don't expose date info
    )


if __name__ == "__main__":
    main()

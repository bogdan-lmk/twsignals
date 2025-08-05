"""Webhook and message data models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class TradingViewWebhook(BaseModel):
    """TradingView webhook payload model."""
    
    ticker: str = Field(..., description="Trading symbol/ticker", min_length=1, max_length=20)
    signal: str = Field(..., description="Trading signal (Buy/Sell)", pattern="^(Buy|Sell)$")
    price: float = Field(..., description="Current price", gt=0)
    time: str = Field(..., description="Timestamp from TradingView")
    interval: Optional[str] = Field(default=None, description="Timeframe/interval")
    chart: Optional[str] = Field(default=None, description="Chart URL")
    
    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        """Validate and normalize ticker symbol."""
        return v.upper().strip()
    
    @field_validator("signal")
    @classmethod
    def validate_signal(cls, v: str) -> str:
        """Validate and normalize signal."""
        return v.capitalize()
    
    @field_validator("price")
    @classmethod
    def validate_price(cls, v: float) -> float:
        """Validate price is positive."""
        if v <= 0:
            raise ValueError("Price must be positive")
        return round(v, 8)  # Round to 8 decimal places for crypto precision
    
    @field_validator("time")
    @classmethod
    def validate_time(cls, v: str) -> str:
        """Validate timestamp format."""
        if not v:
            raise ValueError("Timestamp cannot be empty")
        # Accept various timestamp formats from TradingView
        return v.strip()
    
    @field_validator("chart")
    @classmethod
    def validate_chart_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate chart URL if provided."""
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("Chart URL must be a valid HTTP/HTTPS URL")
        return v
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat(),
        },
        "json_schema_extra": {
            "example": {
                "ticker": "BTCUSDT",
                "signal": "Buy",
                "price": 45000.0,
                "time": "2025-01-15T10:30:00Z",
                "interval": "1h",
                "chart": "https://www.tradingview.com/chart/?symbol=BTCUSDT"
            }
        }
    }


class TelegramMessage(BaseModel):
    """Telegram message model."""
    
    chat_id: str = Field(..., description="Telegram chat ID")
    text: str = Field(..., description="Message text", max_length=4096)
    parse_mode: str = Field(default="HTML", description="Message parse mode")
    disable_web_page_preview: bool = Field(default=True, description="Disable web page preview")
    
    @field_validator("text")
    @classmethod
    def validate_text_length(cls, v: str) -> str:
        """Validate message text length."""
        if len(v) > 4096:
            raise ValueError("Message text cannot exceed 4096 characters")
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "chat_id": "@trading_signals",
                "text": "<b>BTCUSDT</b> (1h)\nSignal: <i>Buy</i>  Price: 45000.0\n🕒 2025-01-15T10:30:00Z",
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
        }
    }


class WebhookResponse(BaseModel):
    """Webhook response model."""
    
    status: str = Field(..., description="Response status")
    message: Optional[str] = Field(default=None, description="Response message")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracking")
    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.utcnow(), description="Response timestamp")
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat(),
        },
        "json_schema_extra": {
            "example": {
                "status": "success",
                "message": "Webhook processed successfully",
                "request_id": "123e4567-e89b-12d3-a456-426614174000",
                "timestamp": "2025-01-15T10:30:00.123456Z"
            }
        }
    }
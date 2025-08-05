"""Application configuration management."""

import os
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application settings
    app_name: str = Field(default="TradingView Telegram Webhook", description="Application name")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=int(os.getenv("PORT", "8000")), description="Server port")
    
    # TradingView webhook settings
    tv_webhook_secret: str = Field(..., description="TradingView webhook HMAC secret")
    
    # Telegram Bot settings
    tg_bot_token: str = Field(..., description="Telegram Bot API token")
    tg_chat_id: str = Field(..., description="Telegram chat ID or @username")
    tg_timeout: int = Field(default=10, description="Telegram API timeout in seconds")
    tg_retry_attempts: int = Field(default=3, description="Number of retry attempts for Telegram API")
    tg_retry_delay: float = Field(default=1.0, description="Initial retry delay in seconds")
    tg_retry_backoff: float = Field(default=2.0, description="Retry backoff multiplier")
    
    # Performance settings
    webhook_timeout: float = Field(default=0.15, description="Webhook response timeout (150ms)")
    cache_ttl: int = Field(default=300, description="Cache TTL for idempotency in seconds")
    
    # Security settings
    allowed_hosts: list[str] = Field(default=["*"], description="Allowed hosts for CORS")
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    @field_validator("tg_chat_id")
    @classmethod
    def validate_chat_id(cls, v: str) -> str:
        """Validate Telegram chat ID format."""
        if not v:
            raise ValueError("Telegram chat ID cannot be empty")
        # Allow both numeric IDs and @username format
        if not (v.startswith("@") or v.lstrip("-").isdigit()):
            raise ValueError("Chat ID must be numeric or start with @")
        return v
    
    @field_validator("tg_retry_attempts")
    @classmethod
    def validate_retry_attempts(cls, v: int) -> int:
        """Validate retry attempts."""
        if v < 0 or v > 10:
            raise ValueError("Retry attempts must be between 0 and 10")
        return v
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.debug or os.getenv("ENVIRONMENT", "").lower() in ["dev", "development"]
    
    @property
    def telegram_base_url(self) -> str:
        """Get Telegram Bot API base URL."""
        return f"https://api.telegram.org/bot{self.tg_bot_token}"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance."""
    return settings
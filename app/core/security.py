"""Security utilities including HMAC signature validation."""

import hashlib
import hmac
from typing import Optional

from .config import get_settings
from .logging import get_logger

logger = get_logger(__name__)


class SignatureError(Exception):
    """Raised when signature validation fails."""
    pass


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    Verify HMAC SHA-256 signature from TradingView webhook.
    
    Args:
        payload: Raw request body bytes
        signature: Signature from X-Signature header
        
    Returns:
        True if signature is valid, False otherwise
        
    Raises:
        SignatureError: If signature validation fails
    """
    settings = get_settings()
    
    if not signature:
        logger.warning("Missing signature in webhook request")
        raise SignatureError("Missing signature")
    
    if not settings.tv_webhook_secret:
        logger.error("TradingView webhook secret not configured")
        raise SignatureError("Webhook secret not configured")
    
    try:
        # Create HMAC SHA-256 hash of the payload
        mac = hmac.new(
            settings.tv_webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        )
        expected_signature = mac.hexdigest()
        
        # Use constant-time comparison to prevent timing attacks
        is_valid = hmac.compare_digest(expected_signature, signature)
        
        if not is_valid:
            logger.warning(
                "Invalid webhook signature",
                expected_length=len(expected_signature),
                received_length=len(signature),
                payload_size=len(payload)
            )
            raise SignatureError("Invalid signature")
        
        logger.debug("Webhook signature validated successfully")
        return True
        
    except Exception as e:
        logger.error("Error validating webhook signature", error=str(e))
        if isinstance(e, SignatureError):
            raise
        raise SignatureError(f"Signature validation error: {str(e)}")


def generate_webhook_signature(payload: bytes, secret: Optional[str] = None) -> str:
    """
    Generate HMAC SHA-256 signature for testing purposes.
    
    Args:
        payload: Raw payload bytes
        secret: Secret key (uses configured secret if not provided)
        
    Returns:
        Hexadecimal signature string
    """
    settings = get_settings()
    secret_key = secret or settings.tv_webhook_secret
    
    if not secret_key:
        raise ValueError("Secret key is required")
    
    mac = hmac.new(
        secret_key.encode('utf-8'),
        payload,
        hashlib.sha256
    )
    return mac.hexdigest()
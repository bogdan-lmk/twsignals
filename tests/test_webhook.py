"""Tests for webhook functionality."""

import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import app
from app.core.security import generate_webhook_signature
from app.models.webhook import TradingViewWebhook


client = TestClient(app)


@pytest.fixture
def sample_webhook_data():
    """Sample webhook data for testing."""
    return {
        "ticker": "BTCUSDT",
        "signal": "Buy",
        "price": 45000.0,
        "time": "2025-01-15T10:30:00Z",
        "interval": "1h",
        "chart": "https://www.tradingview.com/chart/?symbol=BTCUSDT"
    }


@pytest.fixture
def webhook_secret():
    """Test webhook secret."""
    return "test_secret_key_for_hmac_validation"


class TestWebhookEndpoint:
    """Test cases for the webhook endpoint."""
    
    def test_webhook_missing_signature(self, sample_webhook_data):
        """Test webhook request without signature."""
        response = client.post(
            "/webhook",
            json=sample_webhook_data
        )
        assert response.status_code == 403
        assert "Invalid or missing signature" in response.json()["detail"]
    
    def test_webhook_invalid_signature(self, sample_webhook_data):
        """Test webhook request with invalid signature."""
        response = client.post(
            "/webhook",
            json=sample_webhook_data,
            headers={"X-Signature": "invalid_signature"}
        )
        assert response.status_code == 403
    
    @patch("app.core.config.get_settings")
    @patch("app.services.telegram.TelegramService.send_trading_signal")
    def test_webhook_valid_request(
        self, 
        mock_telegram_send, 
        mock_settings,
        sample_webhook_data,
        webhook_secret
    ):
        """Test valid webhook request."""
        # Mock settings
        mock_settings.return_value.tv_webhook_secret = webhook_secret
        mock_settings.return_value.webhook_timeout = 0.15
        mock_settings.return_value.cache_ttl = 300
        
        # Mock Telegram service
        mock_telegram_send.return_value = {
            "ok": True,
            "result": {"message_id": 123}
        }
        
        # Generate valid signature
        payload = json.dumps(sample_webhook_data).encode()
        signature = generate_webhook_signature(payload, webhook_secret)
        
        with patch("app.api.webhook.TelegramService") as mock_service:
            mock_instance = AsyncMock()
            mock_instance.send_trading_signal.return_value = {
                "ok": True,
                "result": {"message_id": 123}
            }
            mock_service.return_value.__aenter__.return_value = mock_instance
            
            response = client.post(
                "/webhook",
                json=sample_webhook_data,
                headers={"X-Signature": signature}
            )
        
        assert response.status_code == 202
        response_data = response.json()
        assert response_data["status"] == "accepted"
        assert "request_id" in response_data
    
    def test_webhook_invalid_json(self, webhook_secret):
        """Test webhook with invalid JSON payload."""
        with patch("app.core.config.get_settings") as mock_settings:
            mock_settings.return_value.tv_webhook_secret = webhook_secret
            
            payload = b"invalid json"
            signature = generate_webhook_signature(payload, webhook_secret)
            
            response = client.post(
                "/webhook",
                data=payload,
                headers={
                    "X-Signature": signature,
                    "Content-Type": "application/json"
                }
            )
        
        assert response.status_code == 400
        assert "Invalid JSON payload" in response.json()["detail"]
    
    def test_webhook_invalid_data_format(self, webhook_secret):
        """Test webhook with invalid data format."""
        with patch("app.core.config.get_settings") as mock_settings:
            mock_settings.return_value.tv_webhook_secret = webhook_secret
            
            invalid_data = {"ticker": ""}  # Missing required fields
            payload = json.dumps(invalid_data).encode()
            signature = generate_webhook_signature(payload, webhook_secret)
            
            response = client.post(
                "/webhook",
                json=invalid_data,
                headers={"X-Signature": signature}
            )
        
        assert response.status_code == 422
        assert "Invalid webhook data" in response.json()["detail"]


class TestHealthEndpoints:
    """Test cases for health check endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "TradingView Telegram Webhook"
        assert data["version"] == "0.1.0"
        assert data["status"] == "running"
    
    def test_health_endpoint(self):
        """Test basic health check."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "twsignals-webhook"
    
    @patch("app.services.telegram.TelegramService.test_connection")
    def test_telegram_health_endpoint(self, mock_test_connection):
        """Test Telegram health check."""
        mock_test_connection.return_value = True
        
        with patch("app.services.telegram.TelegramService") as mock_service:
            mock_instance = AsyncMock()
            mock_instance.test_connection.return_value = True
            mock_service.return_value.__aenter__.return_value = mock_instance
            
            response = client.get("/health/telegram")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["telegram_connected"] is True


class TestDataModels:
    """Test cases for data models."""
    
    def test_trading_view_webhook_validation(self):
        """Test TradingView webhook data validation."""
        valid_data = {
            "ticker": "btcusdt",  # Should be uppercased
            "signal": "buy",      # Should be capitalized
            "price": 45000.123456789,  # Should be rounded
            "time": "2025-01-15T10:30:00Z",
            "interval": "1h",
            "chart": "https://example.com/chart"
        }
        
        webhook = TradingViewWebhook(**valid_data)
        assert webhook.ticker == "BTCUSDT"
        assert webhook.signal == "Buy"
        assert webhook.price == 45000.12345679  # Rounded to 8 decimals
    
    def test_trading_view_webhook_invalid_signal(self):
        """Test webhook with invalid signal."""
        with pytest.raises(ValueError):
            TradingViewWebhook(
                ticker="BTCUSDT",
                signal="InvalidSignal",
                price=45000.0,
                time="2025-01-15T10:30:00Z"
            )
    
    def test_trading_view_webhook_negative_price(self):
        """Test webhook with negative price."""
        with pytest.raises(ValueError):
            TradingViewWebhook(
                ticker="BTCUSDT",
                signal="Buy",
                price=-100.0,
                time="2025-01-15T10:30:00Z"
            )
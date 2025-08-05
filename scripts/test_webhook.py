#!/usr/bin/env python3
"""
Test script for TradingView Telegram Webhook Service.

This script sends a test webhook request to the local service
to verify everything is working correctly.
"""

import json
import requests
import hashlib
import hmac
import os
import sys
from datetime import datetime


def generate_signature(payload: bytes, secret: str) -> str:
    """Generate HMAC SHA-256 signature."""
    mac = hmac.new(secret.encode('utf-8'), payload, hashlib.sha256)
    return mac.hexdigest()


def test_webhook(
    base_url: str = "http://localhost:8000",
    webhook_secret: str = None
):
    """Test the webhook endpoint."""
    
    # Get webhook secret from environment or parameter
    if not webhook_secret:
        webhook_secret = os.getenv("TV_WEBHOOK_SECRET")
        if not webhook_secret:
            print("❌ Please set TV_WEBHOOK_SECRET environment variable")
            print("   or pass it as a parameter")
            return False
    
    # Sample webhook payload
    test_payload = {
        "ticker": "BTCUSDT",
        "signal": "Buy",
        "price": 45000.0,
        "time": datetime.utcnow().isoformat() + "Z",
        "interval": "1h",
        "chart": "https://www.tradingview.com/chart/?symbol=BTCUSDT"
    }
    
    print("🚀 Testing TradingView Telegram Webhook Service")
    print("=" * 50)
    print(f"Base URL: {base_url}")
    print(f"Test payload: {json.dumps(test_payload, indent=2)}")
    print()
    
    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    print()
    
    # Test 2: Telegram health check
    print("2. Testing Telegram connectivity...")
    try:
        response = requests.get(f"{base_url}/health/telegram", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("telegram_connected"):
                print("✅ Telegram connectivity check passed")
            else:
                print("⚠️  Telegram connectivity check failed")
                print(f"   Response: {data}")
        else:
            print(f"❌ Telegram health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Telegram health check error: {e}")
    
    print()
    
    # Test 3: Webhook without signature (should fail)
    print("3. Testing webhook without signature (should fail)...")
    try:
        response = requests.post(
            f"{base_url}/webhook",
            json=test_payload,
            timeout=5
        )
        if response.status_code == 403:
            print("✅ Correctly rejected request without signature")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"❌ Test error: {e}")
    
    print()
    
    # Test 4: Webhook with invalid signature (should fail)
    print("4. Testing webhook with invalid signature (should fail)...")
    try:
        response = requests.post(
            f"{base_url}/webhook",
            json=test_payload,
            headers={"X-Signature": "invalid_signature"},
            timeout=5
        )
        if response.status_code == 403:
            print("✅ Correctly rejected request with invalid signature")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"❌ Test error: {e}")
    
    print()
    
    # Test 5: Valid webhook request
    print("5. Testing valid webhook request...")
    try:
        payload_bytes = json.dumps(test_payload).encode('utf-8')
        signature = generate_signature(payload_bytes, webhook_secret)
        
        response = requests.post(
            f"{base_url}/webhook",
            json=test_payload,
            headers={"X-Signature": signature},
            timeout=5
        )
        
        if response.status_code == 202:
            print("✅ Valid webhook request accepted")
            data = response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   Request ID: {data.get('request_id')}")
            print("   🎉 Telegram message should be sent shortly!")
        else:
            print(f"❌ Webhook request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False
    
    print()
    print("=" * 50)
    print("✅ All tests completed!")
    print("\n💡 Tips:")
    print("   - Check your Telegram chat for the test message")
    print("   - Monitor logs for any errors")
    print("   - Verify your .env configuration if tests failed")
    
    return True


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test TradingView Telegram Webhook Service"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the webhook service (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--secret",
        help="Webhook secret (default: use TV_WEBHOOK_SECRET env var)"
    )
    
    args = parser.parse_args()
    
    success = test_webhook(args.url, args.secret)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
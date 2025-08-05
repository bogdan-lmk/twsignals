#!/usr/bin/env python3
"""
Setup script for TradingView Telegram Webhook Service.

This script helps set up the development environment and configuration.
"""

import os
import secrets
import sys
from pathlib import Path


def generate_webhook_secret() -> str:
    """Generate a secure webhook secret."""
    return secrets.token_hex(32)


def create_env_file():
    """Create .env file from template if it doesn't exist."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✓ .env file already exists")
        return
    
    if not env_example.exists():
        print("✗ .env.example template not found")
        return
    
    # Generate webhook secret
    webhook_secret = generate_webhook_secret()
    
    # Read template and replace placeholders
    template_content = env_example.read_text()
    env_content = template_content.replace(
        "TV_WEBHOOK_SECRET=your_webhook_secret_here",
        f"TV_WEBHOOK_SECRET={webhook_secret}"
    )
    
    # Write .env file
    env_file.write_text(env_content)
    print(f"✓ Created .env file with generated webhook secret")
    print(f"  Webhook secret: {webhook_secret}")
    print("  Please update TG_BOT_TOKEN and TG_CHAT_ID in .env")


def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version < (3, 9):
        print(f"✗ Python {version.major}.{version.minor} is not supported")
        print("  Please use Python 3.9 or higher")
        return False
    
    print(f"✓ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True


def install_dependencies():
    """Install Python dependencies."""
    print("Installing Python dependencies...")
    os.system("pip install -r requirements.txt")
    print("✓ Dependencies installed")


def main():
    """Main setup function."""
    print("🚀 TradingView Telegram Webhook Service Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create .env file
    create_env_file()
    
    # Install dependencies
    try:
        install_dependencies()
    except Exception as e:
        print(f"✗ Failed to install dependencies: {e}")
        print("  Please run: pip install -r requirements.txt")
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed!")
    print("\nNext steps:")
    print("1. Update .env file with your Telegram bot token and chat ID")
    print("2. Run the service: python main.py")
    print("3. Test with: curl http://localhost:8000/health")
    print("4. Configure TradingView alerts to use your webhook URL")
    print("\nFor more information, see README.md")


if __name__ == "__main__":
    main()
# TradingView to Telegram Webhook Service

A fast, reliable webhook service that forwards TradingView alerts to Telegram channels/chats. Built with FastAPI for high performance and low latency.

## 🚀 Features

- **Fast Response**: < 150ms webhook response time requirement
- **Secure**: HMAC SHA-256 signature validation
- **Reliable**: Retry logic with exponential backoff for Telegram API
- **Scalable**: Async/await architecture with background processing
- **Observable**: Structured logging with request IDs
- **Production Ready**: Docker support, health checks, proper error handling

## 📋 Requirements

- Python 3.9+
- TradingView Pro account (for webhook alerts)
- Telegram Bot Token
- Target Telegram channel/chat

## 🛠️ Installation

### Option 1: Cloud Deployment (Recommended) ☁️

**⚠️ ВАЖНО:** TradingView не может подключиться к localhost. Нужно развернуть в облаке!

**Deploy to Render.com (FREE):**
1. Fork this repository to your GitHub
2. Create account on [render.com](https://render.com)
3. Follow [DEPLOYMENT.md](DEPLOYMENT.md) guide
4. Get your webhook URL: `https://your-app.onrender.com/webhook`
5. Use this URL in TradingView instead of localhost

### Option 2: Local Development (для разработки)

1. Clone and setup:
```bash
git clone <repository-url>
cd twsignals
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the service:
```bash
python main.py
# or
uvicorn app.main:app --reload
```

## ⚙️ Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `TV_WEBHOOK_SECRET` | HMAC secret for signature validation | `a1b2c3d4...` |
| `TG_BOT_TOKEN` | Telegram Bot API token | `1234567890:ABC...` |
| `TG_CHAT_ID` | Target chat ID or @username | `@trading_signals` |

### Optional Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug mode |
| `LOG_LEVEL` | `INFO` | Logging level |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |
| `TG_TIMEOUT` | `10` | Telegram API timeout (seconds) |
| `TG_RETRY_ATTEMPTS` | `3` | Number of retry attempts |
| `WEBHOOK_TIMEOUT` | `0.15` | Max webhook response time (seconds) |
| `CACHE_TTL` | `300` | Idempotency cache TTL (seconds) |

## 🔐 Setup Guide

### 1. Create Telegram Bot

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Use `/newbot` command to create a new bot
3. Copy the bot token provided
4. Add your bot to the target channel/group as admin

### 2. Get Chat ID

For channels/groups:
- Use `@channel_name` format, or
- Get numeric ID from bot API

For private chats:
- Send a message to your bot
- Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
- Find your chat ID in the response

### 3. Generate Webhook Secret

```bash
openssl rand -hex 32
```

### 4. Configure TradingView Alert

In TradingView:
1. Create or edit an alert
2. Set webhook URL: `https://yourdomain.com/webhook`
3. Set message format:
```json
{
  "ticker": "{{ticker}}",
  "signal": "{{strategy.order.action}}",
  "price": {{close}},
  "time": "{{timenow}}",
  "interval": "{{interval}}",
  "chart": "https://www.tradingview.com/chart/?symbol={{ticker}}"
}
```
4. Add custom header: `X-Signature: <your_webhook_secret>`

## 📊 API Endpoints

### POST /webhook
Main webhook endpoint for TradingView alerts.

**Headers:**
- `X-Signature`: HMAC SHA-256 signature

**Body:**
```json
{
  "ticker": "BTCUSDT",
  "signal": "Buy",
  "price": 45000.0,
  "time": "2025-01-15T10:30:00Z",
  "interval": "1h",
  "chart": "https://www.tradingview.com/chart/?symbol=BTCUSDT"
}
```

**Response:**
```json
{
  "status": "accepted",
  "message": "Webhook received and processing",
  "request_id": "123e4567-e89b-12d3-a456-426614174000",
  "timestamp": "2025-01-15T10:30:00.123456Z"
}
```

### GET /health
Health check endpoint.

### GET /health/telegram
Telegram API connectivity check.

### GET /
Service information and status.

## 📝 Message Format

Messages sent to Telegram follow this format:

```
BTCUSDT (1h)
Signal: Buy  Price: 45000.0
🕒 2025-01-15T10:30:00Z
📈 Chart
```

## 🔍 Monitoring and Logging

The service provides structured logging with:
- Request IDs for tracing
- Processing times
- Error details
- Telegram delivery status

### Log Levels
- `DEBUG`: Detailed debugging information
- `INFO`: General information (default)
- `WARNING`: Warning messages
- `ERROR`: Error conditions
- `CRITICAL`: Critical errors

### Health Checks
- `/health`: Basic service health
- `/health/telegram`: Telegram API connectivity
- Docker health check every 30 seconds

## 🚦 Error Handling

### Signature Validation
- Invalid or missing signatures return `403 Forbidden`
- All requests must include valid HMAC SHA-256 signature

### Telegram Delivery
- Automatic retries with exponential backoff
- Rate limiting protection (30 messages/second)
- Failed deliveries are logged but don't affect webhook response

### Idempotency
- Duplicate messages are filtered based on ticker, signal, and timestamp
- Configurable cache TTL (default: 5 minutes)

## 🏗️ Architecture

```
TradingView Alert → Webhook (FastAPI) → Background Task → Telegram API
                      ↓
                   < 150ms Response
```

Key design decisions:
- **Fast Response**: Webhook responds immediately, processes in background
- **Async Processing**: Non-blocking I/O for all operations
- **Retry Logic**: Robust error handling with backoff
- **Security**: HMAC signature validation
- **Observability**: Structured logging with request tracking

## 🔧 Development

### Running Tests
```bash
pytest
```

### Code Quality
```bash
# Format code
black .

# Lint code
ruff check .

# Type checking
mypy app/
```

### Building Docker Image
```bash
docker build -t twsignals:latest .
```

## 📈 Performance

- **Response Time**: < 150ms webhook response
- **Throughput**: Handles multiple concurrent webhooks
- **Memory Usage**: ~50MB runtime footprint
- **Rate Limiting**: Respects Telegram API limits (30 msg/sec)

## 🛡️ Security

- HMAC SHA-256 signature validation
- Environment-based configuration
- Non-root Docker container
- No sensitive data in logs
- Input validation and sanitization

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 🆘 Troubleshooting

### Common Issues

**"Invalid signature" error:**
- Check your `TV_WEBHOOK_SECRET` matches TradingView configuration
- Ensure secret is properly base64/hex encoded

**Messages not delivered:**
- Verify bot token and chat ID
- Check bot has admin permissions in target channel
- Review logs for Telegram API errors

**Webhook timeouts:**
- Check service health endpoints
- Verify Docker container is running
- Review resource limits and scaling

### Getting Help

1. Check the logs: `docker-compose logs webhook`
2. Test health endpoints: `curl http://localhost:8000/health`
3. Verify Telegram connectivity: `curl http://localhost:8000/health/telegram`

## 📞 Support

For issues and questions:
- Check the [Issues](https://github.com/your-org/twsignals/issues) page
- Review the troubleshooting section above
- Create a new issue with detailed information
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a TradingView to Telegram webhook service project (twsignals) designed to instantly deliver trading signals from TradingView indicators to Telegram chats. The project follows an MVP-first approach with plans for scaling.

## Architecture Goals

The project is planned with two architectural variants:

**Variant A (MVP - "Simple and Fast")**:
- Python + Flask/FastAPI with single webhook endpoint `/webhook`
- Single-instance hosting (Render/Railway/Heroku)
- Direct Telegram Bot API integration
- HMAC SHA-256 signature verification
- No persistent storage (logs only)
- Target: <10 signals/minute, minimal budget

**Variant B (Production - "Reliable and Scalable")**:
- API Gateway + FastAPI (serverless)
- Message queue (SQS/RabbitMQ) with workers
- PostgreSQL/Redis for configuration and history
- Prometheus/Grafana monitoring
- Target: High volume, multiple chats, SLA requirements

## Key Technical Requirements

### TradingView Integration
- Webhook endpoint: `POST /webhook`
- Expected JSON payload format:
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
- Security: HMAC SHA-256 signature in `X-Signature` header
- Response: 200 status within ≤150ms

### Telegram Message Format
```
<b>{{ticker}}</b>  ({{interval}})
Signal: <i>{{signal}}</i>  Price: {{price}}
🕒 {{time}}
📈 {{chart}}
```

### Performance Requirements
- Delivery SLA: ≥99% uptime during business hours
- Latency: <5 seconds from signal to Telegram delivery
- Rate limiting: Respect Telegram Bot API limits (30 messages/sec)
- Retry logic: 3 attempts with backoff (1s/2s/5s)
- Idempotency: Filter duplicates by (ticker, time, signal)

## Development Approach

### MVP Implementation Strategy
1. Start with Variant A (MVP) for rapid deployment
2. Upgrade to Variant B when reaching 200 messages/day or requiring history/multiple chats
3. Security-first: HMAC validation, HTTPS, secure token storage
4. Observability: correlation request_id, structured logging, success/error counters

### Configuration Management
- MVP: Environment variables
- Production: Configuration files or database storage

### Testing Strategy
- Local webhook emulation
- Telegram dry-run mode for testing
- End-to-end testing with real TradingView alerts
- Negative testing: invalid signatures, empty payloads, timeouts

## Implementation Phases

### Sprint 1 (MVP - 1-2 days)
- Basic FastAPI/Flask setup with `/webhook` endpoint
- HMAC signature validation and payload schema
- Telegram Bot API integration with message templating
- Deployment to cloud platform with HTTPS
- TradingView alert configuration documentation
- End-to-end testing

### Sprint 2 (Stabilization - 1-2 days)
- Retry mechanism with throttling
- Idempotency caching
- Health checks and basic metrics
- Error logging and alerting
- Docker containerization and CI/CD (GitHub Actions)

## Risk Mitigation
- Duplicate signals: Implement idempotency with TTL cache
- Telegram rate limits: Local throttling and queuing
- Service unavailability: Health checks and monitoring alerts
- TradingView template changes: Contract testing and schema validation

## Acceptance Criteria
- Webhook accepts valid JSON, rejects invalid signatures (403)
- Real TradingView signals delivered to Telegram within 5 seconds
- Structured logging with request_id and delivery status
- Complete setup documentation for TradingView configuration
- Robust error handling for network timeouts and API failures
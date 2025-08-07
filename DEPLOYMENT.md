# 🚀 Deployment Guide - Развертывание TradingView Webhook Service

## 🎯 Цель
Развернуть webhook сервис в облаке для получения алертов от TradingView

---

## 🌐 Вариант 1: Render.com (РЕКОМЕНДУЕТСЯ - БЕСПЛАТНО)

### Шаг 1: Подготовка репозитория

1. **Создайте GitHub репозиторий** (если его еще нет):
   ```bash
   git init
   git add .
   git commit -m "Initial commit: TradingView Telegram webhook service"
   git branch -M main
   git remote add origin https://github.com/USERNAME/twsignals.git
   git push -u origin main
   ```

### Шаг 2: Регистрация на Render.com

1. Перейдите на [render.com](https://render.com)
2. Зарегистрируйтесь через GitHub
3. Подключите ваш GitHub аккаунт

### Шаг 3: Создание Web Service

1. **Dashboard → New → Web Service**
2. **Connect repository**: выберите ваш `twsignals` репозиторий
3. **Настройки сервиса:**
   - **Name**: `twsignals-webhook`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Plan**: `Free` (достаточно для начала)

### Шаг 4: Environment Variables

В разделе **Environment** добавьте переменные:

```
HOST=0.0.0.0
PORT=10000
DEBUG=false
LOG_LEVEL=INFO

# TradingView Settings
TV_WEBHOOK_SECRET=123

# Telegram Settings
TG_BOT_TOKEN=123
TG_CHAT_ID=-1002251027945

# Optional Settings
TG_TIMEOUT=10
TG_RETRY_ATTEMPTS=3
TG_RETRY_DELAY=1.0
TG_RETRY_BACKOFF=2.0
WEBHOOK_TIMEOUT=0.15
CACHE_TTL=300
ALLOWED_HOSTS=["*"]
```

### Шаг 5: Deploy

1. **Create Web Service**
2. Дождитесь завершения деплоя (5-10 минут)
3. Получите ваш URL: `https://twsignals-webhook-abc123.onrender.com`

### Шаг 6: Проверка

```bash
# Проверка здоровья сервиса
curl https://your-app-name.onrender.com/health

# Должен вернуть:
# {"status":"healthy","timestamp":...}
```

---

## 🔧 Вариант 2: ngrok (для тестирования)

### Быстрый запуск для тестирования:

1. **Установите ngrok:**
   ```bash
   # macOS
   brew install ngrok/ngrok/ngrok
   
   # или скачайте с https://ngrok.com/download
   ```

2. **Зарегистрируйтесь и получите authtoken:**
   ```bash
   ngrok config add-authtoken YOUR_AUTHTOKEN
   ```

3. **Запустите локальный сервис:**
   ```bash
   source venv/bin/activate
   python main.py
   ```

4. **В новом терминале создайте туннель:**
   ```bash
   ngrok http 8000
   ```

5. **Получите публичный URL:**
   ```
   Forwarding: https://abc123.ngrok.io -> http://localhost:8000
   ```

6. **Используйте в TradingView:**
   ```
   https://abc123.ngrok.io/webhook
   ```

---

## 🐳 Вариант 3: Docker на VPS

### Если у вас есть свой сервер:

1. **Подготовьте сервер:**
   ```bash
   # Установите Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   
   # Установите Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

2. **Загрузите код:**
   ```bash
   git clone https://github.com/USERNAME/twsignals.git
   cd twsignals
   ```

3. **Настройте .env файл:**
   ```bash
   cp .env.example .env
   # Отредактируйте .env с вашими настройками
   ```

4. **Запустите:**
   ```bash
   docker-compose up -d
   ```

5. **Настройте Nginx (опционально):**
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

---

## ✅ Проверка развертывания

### 1. Health Check
```bash
curl https://your-deployed-url/health
```

### 2. Webhook Test
```bash
curl -X POST https://your-deployed-url/webhook \
  -H "Content-Type: application/json" \
  -H "X-Signature: 63cad4abdc3c93c0a2c67faf78821031ceadb9e13cf1d2cd3b16f3204b2cb075" \
  -d '{
    "ticker": "BTCUSDT",
    "signal": "Buy",
    "price": 45000.0,
    "time": "2025-08-05T18:30:00Z",
    "interval": "1h",
    "chart": "https://www.tradingview.com/chart/?symbol=BTCUSDT"
  }'
```

### 3. Telegram Check
Проверьте, что сообщение пришло в ваш Telegram чат.

---

## 🎯 Настройка TradingView

После развертывания используйте ваш реальный URL в TradingView:

**Webhook URL**: `https://your-app-name.onrender.com/webhook`

Подробная инструкция в `TRADINGVIEW_SETUP.md`

---

## 🔒 Безопасность

### Production Checklist:
- ✅ HTTPS (автоматически в Render/ngrok)
- ✅ HMAC подпись валидация
- ✅ Environment variables (не хардкод секретов)
- ✅ Rate limiting
- ✅ Structured logging

### Мониторинг:
- Render предоставляет логи в реальном времени
- Health check endpoint: `/health`
- Telegram health check: `/health/telegram`

---

## 🚨 Troubleshooting

### Частые проблемы:

1. **Build failed на Render:**
   - Проверьте requirements.txt
   - Убедитесь, что Python версия совместима

2. **502 Bad Gateway:**
   - Проверьте, что сервис слушает HOST=0.0.0.0
   - Проверьте правильность PORT переменной

3. **Webhook не получает сигналы:**
   - Проверьте URL в TradingView
   - Проверьте X-Signature заголовок
   - Проверьте логи в Render Dashboard

4. **Telegram не отправляет:**
   - Проверьте TG_BOT_TOKEN
   - Проверьте TG_CHAT_ID
   - Проверьте, что бот добавлен в группу

---

## 📈 Scaling

**Free tier Render.com:**
- ✅ Достаточно для личного использования
- ✅ SSL сертификаты
- ✅ Автоматические деплои
- ⚠️ "Засыпает" после 15 минут неактивности

**Upgrade до Paid plan для:**
- Постоянная работа (no sleep)
- Больше ресурсов
- Кастомные домены

Готовы к развертыванию! 🚀

# ⚡ Быстрое развертывание на Render.com

## 🎯 Цель: получить рабочий URL для TradingView за 10 минут

### Шаг 1: Подготовка GitHub (2 минуты)

1. **Создайте GitHub репозиторий:**
   - Перейдите на [github.com](https://github.com)
   - New Repository → `twsignals` → Create

2. **Загрузите код:**
   ```bash
   cd /Users/buyer7/Desktop/project/twsignals
   git init
   git add .
   git commit -m "TradingView Telegram webhook service"
   git branch -M main
   git remote add origin https://github.com/ВАШ_USERNAME/twsignals.git
   git push -u origin main
   ```

### Шаг 2: Render.com развертывание (5 минут)

1. **Регистрация:**
   - Перейдите на [render.com](https://render.com)
   - Sign Up → Connect GitHub

2. **Создание сервиса:**
   - Dashboard → New → Web Service
   - Select Repository → `twsignals`

3. **Настройки:**
   - **Name**: `twsignals-webhook-YOUR_NAME`
   - **Environment**: Python 3
   - **Runtime**: Python 3.11.5 (если есть опция)
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `gunicorn --config gunicorn.conf.py app:app`
   - **Plan**: Free

4. **Environment Variables:**
   Добавьте эти переменные в Advanced → Environment:
   ```
   HOST=0.0.0.0
   PORT=10000
   DEBUG=false
   LOG_LEVEL=INFO
   TV_WEBHOOK_SECRET=a3ba5cc07a4bd30a3c8c6f04e51dbb55ac078a326f259400a1903e603078460e
   TG_BOT_TOKEN=8339371846:AAH-PXS7rseipWlkSvC044xEkr5x79bE2gg
   TG_CHAT_ID=-1002251027945
   TG_TIMEOUT=10
   TG_RETRY_ATTEMPTS=3
   TG_RETRY_DELAY=1.0
   TG_RETRY_BACKOFF=2.0
   WEBHOOK_TIMEOUT=0.15
   CACHE_TTL=300
   ALLOWED_HOSTS=["*"]
   ```

5. **Deploy:**
   - Create Web Service
   - Дождитесь деплоя (3-5 минут)

### Шаг 3: Получите URL (1 минута)

После успешного деплоя вы получите URL:
```
https://twsignals-webhook-YOUR_NAME.onrender.com
```

**Ваш webhook URL:**
```
https://twsignals-webhook-YOUR_NAME.onrender.com/webhook
```

### Шаг 4: Проверка (1 минута)

```bash
# Проверьте здоровье сервиса
curl https://your-app-name.onrender.com/health

# Должен вернуть:
{"status":"healthy","timestamp":...,"service":"twsignals-webhook","version":"0.1.0"}
```

### Шаг 5: TradingView настройка (1 минута)

В TradingView алерте:
1. ✅ Включите "URL вебхука"
2. **URL**: `https://your-app-name.onrender.com/webhook`
3. **Сообщение**: JSON из [TRADINGVIEW_SETUP.md](TRADINGVIEW_SETUP.md)

## 🎉 Готово!

Теперь TradingView может отправлять алерты на ваш webhook!

---

## 🆘 Если что-то не работает

### ❌ "metadata-generation-failed" ошибка:
**Решение:**
1. В Render → Settings → Environment
2. Убедитесь, что Python версия 3.11.5
3. Build Command: `pip install --upgrade pip && pip install -r requirements.txt`
4. Manual Deploy → Clear build cache → Deploy

### ❌ "gunicorn: command not found" ошибка:
**Решение 1 (быстрое):**
1. Settings → General → Start Command
2. Измените на: `python main.py`
3. Save Changes → Manual Deploy

**Решение 2 (рекомендуемое):**
1. Start Command: `gunicorn --config gunicorn.conf.py app:app`
2. Manual Deploy (gunicorn уже добавлен в requirements)

### ❌ "Build failed" ошибка:
1. Проверьте логи в Render Dashboard
2. Убедитесь, что все Environment Variables добавлены
3. Попробуйте Manual Deploy

### TradingView не отправляет:
1. Проверьте URL (должен содержать `/webhook`)
2. Убедитесь, что сервис отвечает на `/health`
3. Проверьте JSON формат в алерте

### Telegram не получает сообщения:
1. Проверьте TG_BOT_TOKEN и TG_CHAT_ID
2. Убедитесь, что бот добавлен в группу
3. Проверьте логи сервиса

---

**💡 Полезные ссылки:**
- 📖 Подробная инструкция: [DEPLOYMENT.md](DEPLOYMENT.md)
- 📱 Настройка TradingView: [TRADINGVIEW_SETUP.md](TRADINGVIEW_SETUP.md)
- 🤖 Render.com Dashboard: https://dashboard.render.com/
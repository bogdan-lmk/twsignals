# 🚀 TradingView Alert Setup Guide

Пошаговая инструкция по настройке алертов TradingView для отправки торговых сигналов в Telegram.

## 📋 Что вам понадобится

1. ✅ **Развернутый webhook сервис в облаке** (Render.com/Railway/Heroku)
2. ✅ **Telegram бот** с токеном и chat ID
3. ✅ **TradingView аккаунт** с доступом к алертам

## ⚠️ ВАЖНО!

**TradingView НЕ МОЖЕТ подключиться к localhost!**
- ❌ `http://localhost:8000/webhook` - НЕ РАБОТАЕТ
- ✅ `https://your-app.onrender.com/webhook` - РАБОТАЕТ

**Нужно сначала развернуть сервис в облаке:** [DEPLOYMENT.md](DEPLOYMENT.md)

## 🔧 Настройка в TradingView

### Шаг 1: Создание алерта

1. Откройте график интересующего вас актива (например, BTCUSDT)
2. Нажмите на кнопку **"Алерт"** (🔔) на панели инструментов
3. Или используйте горячие клавиши: **Alt + A**

### Шаг 2: Настройка условий алерта

1. **Условие**: Выберите ваш индикатор или стратегию
2. **Сообщение**: Выберите типы сигналов (Buy/Sell)
3. **Опции**: Настройте по необходимости

### Шаг 3: Настройка вебхука

В разделе **"Уведомления"**:

1. ✅ Включите **"URL вебхука"**
2. **URL**: Укажите ваш webhook endpoint из облака:
   ```
   https://your-app-name.onrender.com/webhook
   ```
   
   **Примеры правильных URL:**
   - `https://twsignals-webhook.onrender.com/webhook`
   - `https://my-trading-bot.railway.app/webhook`
   - `https://yourdomain.com/webhook`

### Шаг 4: Настройка JSON сообщения

В поле **"Сообщение"** вставьте следующий JSON код:

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

### Шаг 5: Важные настройки

1. **Заголовки HTTP**: 
   - `Content-Type`: `application/json`
   - `X-Signature`: `[будет добавлена автоматически]`

2. **Метод**: POST (по умолчанию)

## 🔐 Настройка подписи (Security)

Ваш webhook secret из `.env` файла:
```
TV_WEBHOOK_SECRET=a3ba5cc07a4bd30a3c8c6f04e51dbb55ac078a326f259400a1903e603078460e
```

**ВАЖНО**: TradingView автоматически создает HMAC SHA-256 подпись для JSON payload.

## 📱 Формат Telegram сообщения

Ваш бот будет отправлять сообщения в следующем формате:

```
🔥 BTCUSDT (1h)
Signal: Buy  Price: 45000.0
🕒 2025-08-05T18:30:00Z
📈 https://www.tradingview.com/chart/?symbol=BTCUSDT
```

## 🧪 Тестирование

### 1. Проверка здоровья сервиса
```bash
curl http://localhost:8000/health
```

### 2. Тест webhook вручную
```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -H "X-Signature: [HMAC-SHA256-подпись]" \
  -d '{
    "ticker": "BTCUSDT",
    "signal": "Buy", 
    "price": 45000.0,
    "time": "2025-08-05T18:30:00Z",
    "interval": "1h",
    "chart": "https://www.tradingview.com/chart/?symbol=BTCUSDT"
  }'
```

## 🔍 Поддерживаемые поля

| Поле | Обязательное | Описание | Пример |
|------|--------------|----------|--------|
| `ticker` | ✅ | Символ актива | `"BTCUSDT"` |
| `signal` | ✅ | Сигнал (Buy/Sell) | `"Buy"` |
| `price` | ✅ | Текущая цена | `45000.0` |
| `time` | ✅ | Временная метка | `"2025-08-05T18:30:00Z"` |
| `interval` | ❌ | Таймфрейм | `"1h"` |
| `chart` | ❌ | Ссылка на график | `"https://..."` |

## ⚠️ Возможные проблемы

### 1. Ошибка 403 "Invalid signature"
- Проверьте правильность webhook secret
- Убедитесь, что JSON формат корректный

### 2. Ошибка 422 "Validation error"
- Проверьте обязательные поля
- Убедитесь, что `signal` содержит "Buy" или "Sell"
- Убедитесь, что `price` положительное число

### 3. Сообщение не приходит в Telegram
- Проверьте бот токен в `.env`
- Проверьте chat ID
- Убедитесь, что бот добавлен в группу/канал

## 📊 Мониторинг

Логи сервиса показывают:
- ✅ Получение webhook
- ✅ Валидацию подписи
- ✅ Отправку в Telegram
- ❌ Ошибки и их причины

Пример успешного лога:
```
2025-08-05 18:33:14 - INFO - Message sent successfully - message_id: 2
```

## 🚀 Готово!

После настройки ваши TradingView алерты будут автоматически отправляться в Telegram через ваш webhook сервис.

**Webhook URL для TradingView**: `http://your-domain.com/webhook`
**Telegram Chat**: `-1002251027945`
**Secret**: `a3ba5cc07a4bd30a3c8c6f04e51dbb55ac078a326f259400a1903e603078460e`
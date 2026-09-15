# Telegram Troll Bot

Умный бот-тролль для Telegram-чатов.  
Случайно (15–25%) подъебывает участников в стиле свежего чувака, который шарит за TikTok / X / Instagram.

### Возможности
- Контекстные подъёбы через бесплатный ИИ (OpenRouter)
- Микс русского + английского сленга
- Работает 24/7 без твоего компьютера

### Быстрый старт

1. Создай бота через [@BotFather](https://t.me/BotFather) → получи токен
2. Получи бесплатный ключ на [openrouter.ai](https://openrouter.ai) → Keys → Create Key
3. Добавь бота в чат и сделай админом

### Локальный запуск

```bash
cp .env.example .env
# заполни BOT_TOKEN и OPENROUTER_API_KEY
pip install -r requirements.txt
python main.py
```

### Деплой 24/7 (рекомендуется)

**Koyeb** (не засыпает):
1. Залей этот репозиторий на GitHub
2. Зайди на [koyeb.com](https://www.koyeb.com) → Deploy from GitHub
3. Добавь переменные окружения:
   - `BOT_TOKEN`
   - `OPENROUTER_API_KEY`
   - `ROAST_CHANCE=0.20`
4. Build: `pip install -r requirements.txt`
5. Run: `python main.py`

**Render** (бесплатно):
1. New → Web Service → подключи репозиторий
2. Те же переменные
3. Чтобы не засыпал — поставь UptimeRobot на пинг раз в 10 минут

### Настройки
- `ROAST_CHANCE` — вероятность ответа (0.15–0.25 рекомендуется)

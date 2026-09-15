import asyncio
import os
import random

from aiohttp import web
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, Update
from openai import AsyncOpenAI

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
ROAST_CHANCE = float(os.getenv("ROAST_CHANCE", "0.20"))
PORT = int(os.getenv("PORT", "10000"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL") or os.getenv("RENDER_EXTERNAL_URL") or "https://poopovalex-4.onrender.com"
WEBHOOK_PATH = "/telegram/webhook"

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY is not set")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

client = AsyncOpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)

SYSTEM_PROMPT = """Ты — грубый, наглый Telegram roast-тролль. Твоя задача — отвечать так, как реально отвечает токсичный друг в групповом чате, а не как стендапер и не как нейросеть.

ГЛАВНОЕ:
- Ответ должен быть КОРОТКИМ: обычно 3–10 слов, максимум одно короткое предложение.
- Сначала посмотри, что человек написал, и найди самый очевидный повод подъебать именно это сообщение.
- Не сочиняй сложные метафоры и не объясняй шутку.
- Не пытайся быть «умным комиком». Чем естественнее и тупее выглядит подъёб, тем лучше.
- Пиши разговорно, будто это мгновенный ответ в Telegram.
- Мат разрешён и часто желателен: «бля», «ебать», «нахуй», «хуесос», «долбоёб», «ебанат», «пиздец», «хуйня», «клоун», «нытик», «ленивый» и т.п.
- Не надо делать каждую фразу максимально длинной или интеллектуальной.
- Не используй англоязычный TikTok-сленг просто ради него. Никаких обязательных «aura points / NPC / main character / skill issue» в каждом ответе.

СТИЛЬ:
Предпочитай простые естественные конструкции:
- «ты ленивый хуесос потому что»
- «ебать ты нытик»
- «ну ты и долбоёб»
- «какой же ты клоун»
- «тебе лишь бы хуйню написать»
- «ты чё за ебанат»
- «понятно, опять хуйню высрал»
- «иди погуляй, миллениал»
- «ебать ты миллениал»
- «ну ты и даттебае»
- «даттебае, иди делом займись»

«миллениал» и «даттебае» можно использовать как абсурдные оскорбительные обращения, но НЕ вставляй их постоянно. Они должны появляться неожиданно и к месту.

Примеры:
Сообщение: «бля, я не пойду гулять»
Ответ: «ты ленивый хуесос потому что»

Сообщение: «я опять проспал»
Ответ: «ебать ты долбоёб»

Сообщение: «не хочу делать домашку»
Ответ: «ты просто ебаный лентяй»

Сообщение: «кто пойдёт в магазин?»
Ответ: «сам иди нахуй, чё ноешь»

Сообщение: «я сегодня ничего не делал»
Ответ: «ебать ты бесполезный»

Сообщение: «мне лень вставать»
Ответ: «миллениал ебаный, вставай»

Сообщение: «я посмотрел этот аниме»
Ответ: «ну ты и даттебае»

Сообщение: «я думаю это хорошая идея»
Ответ: «какой же ты уверенный долбоёб»

Не делай ответы вроде: «Bro, это не hot take, это brainrot с завышенной самооценкой» — это слишком искусственно.
Не используй длинные рассуждения, сравнения, философию или объяснение панча.

ОГРАНИЧЕНИЯ:
Не оскорбляй защищённые характеристики: национальность, расу, религию, инвалидность, ориентацию и т.п. Не выдумывай факты о внешности, семье, деньгах или жизни человека. Подъёбывай только содержание сообщения, его поведение или мнение.

Отвечай ТОЛЬКО готовым коротким roast без пояснений."""


async def generate_roast(user_message: str, username: str) -> str:
    user_message = user_message[:1500].strip()
    username = username[:64].strip()

    try:
        response = await client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Ник: @{username}\n"
                        f"Сообщение: «{user_message}»\n\n"
                        "Найди самый очевидный повод подъебать именно это сообщение. "
                        "Ответь очень коротко, естественно и грубо, как токсичный друг в чате. "
                        "Без анализа и без объяснений."
                    ),
                },
            ],
            temperature=1.15,
            max_tokens=60,
        )

        roast = (response.choices[0].message.content or "").strip()
        if roast:
            return roast[:300]
        raise ValueError("Empty AI response")

    except Exception as e:
        print(f"AI error: {e}")
        fallbacks = [
            f"Бля, @{username}, ну ты и хуесос.",
            f"@{username}, ебать ты клоун.",
            f"Ну ты и долбоёб, @{username}.",
            f"@{username}, опять хуйню высрал.",
            f"Ебать ты нытик, @{username}.",
        ]
        return random.choice(fallbacks)


@dp.message(F.chat.type.in_({"group", "supergroup"}) & F.text)
async def on_message(message: Message):
    if message.from_user.is_bot or (message.text and message.text.startswith("/")):
        return

    if random.random() > ROAST_CHANCE:
        return

    await asyncio.sleep(random.uniform(1.5, 4.0))

    username = message.from_user.username or message.from_user.first_name
    roast = await generate_roast(message.text or "", username)

    try:
        await message.reply(roast)
    except Exception as e:
        print(f"Reply error: {e}")


async def health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "bot": "running"})


async def telegram_webhook(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        update = Update.model_validate(data, context={"bot": bot})
        await dp.feed_update(bot, update)
        return web.json_response({"ok": True})
    except Exception as e:
        print(f"Webhook update error: {e}")
        return web.json_response({"ok": False}, status=500)


async def run_web_server() -> web.AppRunner:
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    app.router.add_post(WEBHOOK_PATH, telegram_webhook)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"Health/webhook server listening on port {PORT}")
    return runner


async def main():
    print("Тролль-бот запускается в webhook-режиме...")
    runner = await run_web_server()
    webhook_url = WEBHOOK_URL.rstrip("/") + WEBHOOK_PATH

    try:
        # ВАЖНО: polling здесь больше не используется.
        # Webhook исключает конфликт getUpdates между экземплярами Render.
        await bot.delete_webhook(drop_pending_updates=True)
        await bot.set_webhook(webhook_url, drop_pending_updates=True)
        print(f"Telegram webhook set: {webhook_url}")
        await asyncio.Event().wait()
    finally:
        try:
            await bot.delete_webhook(drop_pending_updates=False)
        except Exception as e:
            print(f"Webhook cleanup error: {e}")
        await runner.cleanup()
        await bot.session.close()
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import os
import random

from aiohttp import web
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from openai import AsyncOpenAI

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
ROAST_CHANCE = float(os.getenv("ROAST_CHANCE", "0.20"))
PORT = int(os.getenv("PORT", "10000"))

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

SYSTEM_PROMPT = """Ты — свежий, пи*датый тролль в телеграм-чате.
Ты шаришь за всё: TikTok, X (Twitter), Instagram, мемы, тренды.
Ты хочешь реально задеть человека, но делаешь это смешно и остроумно.

Стиль:
- Миксуй русский + английский сленг (rizz, no cap, mid, ratio, skibidi, sigma, gyatt, cringe, vibe, L, W, cooked и т.д.)
- Говори как обычный чувак из чата, который просто лучше всех шарит
- Короткие, острые ответы (1-3 предложения)
- Иногда в формате ratio / "это mid" / "брат ты cooked" / "rizz level: negative"
- Никогда не говори, что ты бот.

Отвечай только текстом подъёба."""


async def generate_roast(user_message: str, username: str) -> str:
    try:
        response = await client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Человек @{username} написал: «{user_message}»\n\nПодъеби его.",
                },
            ],
            temperature=0.95,
            max_tokens=150,
        )
        return (response.choices[0].message.content or "").strip()
    except Exception as e:
        print(f"AI error: {e}")
        fallbacks = [
            f"@{username} брат это mid no cap",
            f"rizz check failed @{username}",
            f"@{username} ты сейчас freefall",
            f"L + ratio + ты cooked @{username}",
            f"@{username} vibe check: failed hard",
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


async def run_web_server() -> web.AppRunner:
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"Health server listening on port {PORT}")
    return runner


async def main():
    print("Тролль-бот запускается...")
    runner = await run_web_server()
    try:
        # Remove an old Telegram webhook before switching to long polling.
        # This is harmless when no webhook is configured.
        await bot.delete_webhook(drop_pending_updates=True)
        print("Telegram webhook cleared. Starting polling...")
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()
        await bot.session.close()
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import os
import random
from collections import deque

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

# Последние ответы передаются модели, чтобы она не повторяла одни и те же панчи.
recent_roasts = deque(maxlen=40)

ROAST_STYLES = [
    "Одно тупое короткое оскорбление по сути сообщения.",
    "Ответ как токсичный друг: максимально буднично и без попытки быть смешным.",
    "Ударь по конкретной детали сообщения, одним коротким панчем.",
    "Сделай сухой и наглый ответ, будто собеседник очевидно облажался.",
    "Абсурдный, но простой подъёб без метафор и философии.",
    "Сделай вид, будто сообщение настолько тупое, что даже отвечать серьёзно не хочется.",
    "Короткий матершинный ответ в стиле комментария под TikTok.",
    "Подъёб через действие: скажи человеку, что ему делать, чтобы усилить шутку.",
    "Подъёб через его жалобу или лень, если это есть в сообщении.",
    "Подъёб через самоуверенность, если человек что-то утверждает.",
    "Подъёб через нытьё, если человек жалуется.",
    "Сухой ответ из 3–6 слов, будто ты даже не удивлён его хуйнёй.",
    "Используй неожиданное слово вроде «миллениал» или «даттебае», если оно реально подходит по абсурдности.",
    "Наглый ответ без мата, если мат не нужен — разнообразь лексику.",
    "Начни с «бля», «ебать», «ну», «ага», «понятно» или вообще без вводного слова — выбери случайно.",
]

SYSTEM_PROMPT = """Ты — грубый, наглый Telegram roast-тролль. Ты отвечаешь как реальный токсичный друг в групповом чате, а НЕ как стендапер и НЕ как нейросеть.

ГЛАВНАЯ ЦЕЛЬ — ОГРОМНОЕ РАЗНООБРАЗИЕ.
Каждый ответ должен ощущаться новым. Не повторяй одну и ту же конструкцию, ритм, ругательство или панч два раза подряд. Не превращайся в генератор «ебать ты + существительное».

ФОРМАТ:
- Обычно 3–10 слов.
- Максимум одно короткое предложение.
- Никаких объяснений и рассуждений.
- Не используй сложные метафоры и заумные сравнения.
- Бей именно по тому, что человек написал.
- Иногда достаточно 2–4 слов.
- Иногда используй мат, иногда нет.
- Иногда обращайся напрямую, иногда вообще без «ты».
- Чередуй начало, длину и структуру.

ЛЕКСИКА:
Используй живой русский чатовый язык: бля, ебать, нахуй, хуесос, долбоёб, ебанат, пиздец, хуйня, клоун, нытик, лентяй, душнила, придурок, дебил, балбес, придурочный, клоун, чёрт, чудо, гений, чемпион и т.п.
Можно иногда использовать «миллениал» и «даттебае» как абсурдные оскорбительные обращения. Не вставляй их часто.
Английский TikTok-сленг НЕ обязателен. Не пихай aura, NPC, bro, skill issue и т.п. без причины.

РАЗНООБРАЗЬ СТРУКТУРУ. Используй разные типы:
- «ты ленивый хуесос»
- «ебать, какой же ты нытик»
- «ну и нахуй ты это написал»
- «понятно, человек опять хуйню придумал»
- «бля, займись уже чем-нибудь»
- «тебе бы сначала самому разобраться»
- «ага, конечно, гений нашёлся»
- «миллениал ебаный»
- «ну ты и даттебае»
- «это сейчас зачем было вообще»
- «сильное заявление от человека, который…» — только если действительно уместно
- «всё понятно, мозг сегодня выходной»
- «иди проспись сначала»
- «какой же ты душный пиздец»
- «хорош, чемпион, продолжай»
- «вот это ты хуйню выдал»

НЕ КОПИРУЙ эти примеры дословно. Они показывают направление, а не готовый список.

КОНТЕКСТ:
Если человек говорит о лени — подъеби за лень.
Если жалуется — подъеби за нытьё.
Если хвастается — подъеби за самоуверенность.
Если задаёт очевидный вопрос — подъеби за вопрос.
Если пишет ерунду — подъеби за ерунду.
Если пишет короткую бытовую фразу — отвечай так же коротко, будто это обычная перепалка.
Если сообщение вообще не даёт повода для умного панча — используй простой бытовой подъёб, а не выдумывай историю о человеке.

ЗАПРЕТ НА ПОВТОРЫ:
Никогда не повторяй дословно недавний ответ. Если среди примеров ниже есть похожая фраза, придумай другую структуру и другие слова.

ОГРАНИЧЕНИЯ:
Не оскорбляй защищённые характеристики: национальность, расу, религию, инвалидность, ориентацию и т.п. Не выдумывай факты о внешности, семье, деньгах или жизни человека. Подъёбывай содержание сообщения, его поведение или мнение.

Отвечай ТОЛЬКО готовым коротким roast."""


async def generate_roast(user_message: str, username: str) -> str:
    user_message = user_message[:1500].strip()
    username = username[:64].strip()
    style = random.choice(ROAST_STYLES)
    recent = "\n".join(f"- {x}" for x in list(recent_roasts)[-15:]) or "нет"

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
                        f"Случайный стиль на этот раз: {style}\n\n"
                        f"Недавние ответы, которые НЕЛЬЗЯ повторять или перефразировать слишком близко:\n{recent}\n\n"
                        "Придумай новый короткий подъёб. Сначала найди повод именно в сообщении, "
                        "потом ответь одной естественной фразой. Не копируй прошлые ответы."
                    ),
                },
            ],
            temperature=1.35,
            max_tokens=70,
        )

        roast = (response.choices[0].message.content or "").strip()
        if roast:
            roast = roast.replace("\n", " ").strip()
            # Защита от почти полного повтора.
            normalized = " ".join(roast.lower().split())
            recent_normalized = {" ".join(x.lower().split()) for x in recent_roasts}
            if normalized in recent_normalized:
                raise ValueError("Repeated roast")
            recent_roasts.append(roast)
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
            f"@{username}, мозг сегодня выходной?",
            f"Бля, @{username}, ну хорош уже.",
            f"@{username}, какой же ты душнила.",
        ]
        roast = random.choice(fallbacks)
        recent_roasts.append(roast)
        return roast


@dp.message(F.chat.type.in_({"group", "supergroup"}) & F.text)
async def on_message(message: Message):
    if message.from_user.is_bot or (message.text and message.text.startswith("/")):
        return

    if random.random() > ROAST_CHANCE:
        return

    await asyncio.sleep(random.uniform(0.15, 0.45))

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

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
recent_roasts = deque(maxlen=60)

RESPONSE_STYLES = [
    "Коротко подколоть человека по сути сообщения.",
    "Ответить как токсичный друг, но без прямого оскорбления.",
    "Сделать сухой саркастичный комментарий.",
    "Дать абсурдную реакцию, будто ситуация абсолютно ненормальная.",
    "Сделать вид, что сообщение — величайшее событие дня.",
    "Ответить с лёгким удивлением: будто ты не ожидал услышать такую хуйню.",
    "Коротко согласиться, но так, чтобы было смешно.",
    "Коротко не согласиться и подколоть аргумент.",
    "Задать один короткий встречный вопрос, который продолжает прикол.",
    "Дать неожиданную бытовую рекомендацию в ответ на сообщение.",
    "Сделать вид, что ты очень серьёзно анализируешь полную ерунду.",
    "Ответить максимально спокойно на абсолютно нелепое сообщение.",
    "Сделать короткое драматичное объявление из обычной бытовой фразы.",
    "Сделать мини-прогноз, что будет дальше.",
    "Ответить как будто ты уже устал от этой истории.",
    "Подхватить ключевое слово из сообщения и переиграть его.",
    "Сделать короткий неожиданный комплимент с подвохом.",
    "Ответить одним очень коротким наблюдением.",
    "Сделать реакцию в духе «ну всё, приехали».",
    "Ответить как будто это обычная перепалка между друзьями.",
    "Использовать мат, но не обязательно оскорбление.",
    "Сделать короткий roast именно за лень, нытьё или самоуверенность, если это видно из текста.",
    "Подколоть конкретную деталь, а не человека целиком.",
    "Сделать сухой ответ из 2–6 слов.",
    "Сделать чуть более разговорный ответ из 6–12 слов.",
    "Иногда использовать «миллениал» или «даттебае» как абсурдную деталь, но только если уместно.",
]

SYSTEM_PROMPT = """Ты — живой персонаж группового Telegram-чата: наглый, смешной, иногда токсичный, но главное — НЕПРЕДСКАЗУЕМЫЙ.

ГЛАВНАЯ ЦЕЛЬ — ОГРОМНОЕ РАЗНООБРАЗИЕ. Ты НЕ должен отвечать на каждое сообщение оскорблением. Иногда подколы, иногда сарказм, иногда абсурдная реакция, иногда вопрос, иногда согласие, иногда мини-совет, иногда наблюдение, иногда просто смешная бытовая фраза. Ответ должен выглядеть как настоящая реакция друга в чате, а не как генератор roast-фраз.

ВАЖНО: примерно половина ответов может вообще НЕ содержать оскорблений. Если сообщение само по себе не требует оскорбления — не оскорбляй. Смешная реакция важнее мата.

ФОРМАТ:
- Обычно 3–12 слов.
- Максимум одно короткое предложение.
- Никаких объяснений, рассуждений и вступлений.
- Иногда 2–4 слова, иногда 8–12.
- Иногда мат, иногда вообще без мата.
- Иногда обращайся напрямую, иногда без «ты».
- Не используй сложные метафоры и заумный юмор.
- Не превращай каждый ответ в панчлайн.
- Не обязательно заканчивать ответ шуткой.

ТИПЫ РЕАКЦИЙ, КОТОРЫЕ НУЖНО ЧЕРЕДОВАТЬ:
1. Подкол: «ну ты конечно кадр».
2. Сарказм: «сильный план, вопросов нет».
3. Абсурд: «всё, отменяем цивилизацию».
4. Сухая реакция: «ну приехали».
5. Смешное согласие: «вот это уже разговор».
6. Смешное несогласие: «нет, это уже какая-то дичь».
7. Встречный вопрос: «и что ты теперь с этим делать будешь?».
8. Бытовой совет: «ложись спать и не усугубляй».
9. Драматизация: «всё, день официально испорчен».
10. Фальшиво серьёзная реакция: «это требует срочного совещания».
11. Наблюдение: «интересно, как мы вообще до этого дошли».
12. Мини-прогноз: «через час будешь жалеть».
13. Неожиданный комплимент: «ладно, звучит подозрительно убедительно».
14. Подхват слова: если человек пишет необычное слово, можно обыграть именно его.
15. Roast: если человек реально просит подколоть, хвастается, ноет или пишет очевидную хуйню — тогда можно жёстко подъебать.

РОУСТ НЕ РАВЕН ОСКОРБЛЕНИЮ:
Можно смешить ситуацией, а не человеком. Можно сказать «вот это поворот», «план века», «ну всё, приехали», «сильное решение», «это уже отдельный вид искусства» и т.п. Не нужно постоянно писать «ты долбоёб», «ты хуесос», «ебать ты клоун».

ЛЕКСИКА:
Используй живой русский чатовый язык. Мат допустим, но дозируй его. Можно иногда: бля, ебать, нахуй, пиздец, хуйня, клоун, нытик, лентяй, душнила, гений, чемпион и т.п.
«Миллениал» и «даттебае» — редкие абсурдные слова, а не обязательная часть каждого ответа.
Не пихай английский TikTok-сленг без причины.

РАЗНООБРАЗЬ НАЧАЛО:
Иногда «бля», иногда «ну», «ага», «понятно», «ебать», «короче», «всё», «ладно», иногда сразу с сути, иногда с вопроса. Не повторяй один и тот же старт подряд.

КОНТЕКСТ:
Если человек ленится — можно подколоть или дать смешной совет.
Если жалуется — можно подколоть, посочувствовать с сарказмом или предложить решение.
Если хвастается — можно подколоть, согласиться с подвохом или раздуть его успех до абсурда.
Если задаёт очевидный вопрос — можно подколоть или ответить очевидностью.
Если пишет ерунду — можно абсурдно отреагировать.
Если сообщает обычную бытовую вещь — не обязан оскорблять; лучше естественная реакция.
Если сообщение серьёзное или требует нормальной реакции — не превращай его автоматически в roast.

ЗАПРЕТ НА ПОВТОРЫ:
Никогда не повторяй дословно недавний ответ. Если среди недавних ответов есть похожая конструкция, придумай другую. Не используй одну и ту же модель вроде «ебать ты + существительное» снова и снова.

ОГРАНИЧЕНИЯ:
Не оскорбляй защищённые характеристики: национальность, расу, религию, инвалидность, ориентацию и т.п. Не выдумывай факты о внешности, семье, деньгах или жизни человека. Реагируй только на содержание сообщения, его мнение, слова или очевидное поведение из текста.

Отвечай ТОЛЬКО готовой короткой реакцией для Telegram."""


async def generate_roast(user_message: str, username: str) -> str:
    user_message = user_message[:1500].strip()
    username = username[:64].strip()
    style = random.choice(RESPONSE_STYLES)
    recent = "\n".join(f"- {x}" for x in list(recent_roasts)[-20:]) or "нет"

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
                        f"Случайный режим ответа: {style}\n\n"
                        f"Недавние ответы, которые НЕЛЬЗЯ повторять или делать слишком похожими:\n{recent}\n\n"
                        "Выбери наиболее естественную реакцию на конкретное сообщение. "
                        "Не обязан оскорблять. Главное — чтобы это звучало как живой человек в групповом чате и отличалось от недавних ответов."
                    ),
                },
            ],
            temperature=1.45,
            max_tokens=70,
        )

        roast = (response.choices[0].message.content or "").strip()
        if roast:
            roast = roast.replace("\n", " ").strip()
            normalized = " ".join(roast.lower().split())
            recent_normalized = {" ".join(x.lower().split()) for x in recent_roasts}
            if normalized in recent_normalized:
                raise ValueError("Repeated response")
            recent_roasts.append(roast)
            return roast[:300]
        raise ValueError("Empty AI response")

    except Exception as e:
        print(f"AI error: {e}")
        fallbacks = [
            f"Бля, @{username}, ну ты даёшь.",
            f"@{username}, это сейчас серьёзно?",
            "Ну всё, приехали.",
            "Сильное решение, вопросов нет.",
            "Ебать, вот это поворот.",
            "План века, одобрено.",
            "Ладно, это уже смешно.",
            "И что теперь с этим делать?",
            "Понятно, день пошёл по пизде.",
            "Ну ты конечно кадр.",
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

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

SYSTEM_PROMPT = """Ты — очень умный и язвительный тролль из телеграм-чата. Твоя задача — делать КОРОТКИЕ, меткие и смешные подъёбы, которые звучат так, будто их придумал реально остроумный человек, а не генератор случайных мемов.

Главный принцип: бей не просто по человеку, а по СОДЕРЖАНИЮ его сообщения. Найди в тексте слабое место: нелогичность, пафос, самоуверенность, странную формулировку, нелепое мнение, очевидное противоречие или смешную деталь — и построй шутку именно вокруг этого.

СТИЛЬ:
- 1–3 коротких предложения. Лучше одна очень точная шутка, чем пять средних.
- Язык — современный разговорный русский. Английский сленг используй только там, где он реально усиливает шутку: cooked, cringe, mid, ratio, L, no cap, skill issue и т.п.
- Можно использовать сарказм, гиперболу, сравнения, неожиданные метафоры, псевдо-диагнозы, сухую иронию и deadpan-юмор.
- Иногда делай вид, что абсолютно серьёзно анализируешь человека, а вывод получается уничтожающий.
- Подъёб должен быть персональным и связанным с конкретным сообщением.
- Не начинай каждый ответ с имени/ника.
- Не используй одни и те же шаблоны вроде «ты cooked», «L + ratio» и «это mid» в каждом ответе. Они должны быть редкими приёмами, а не костылём.
- Не объясняй шутку. Не пиши «шутка», «лол», «ха-ха» и комментарии о том, что ты ИИ.
- Не говори, что ты бот, модель или ассистент.
- Не повторяй сообщение пользователя целиком.
- Не используй эмодзи, если они не нужны для шутки.
- Не переходи в длинные оскорбительные тирады. Сила ответа — в точности.

ВАЖНО:
- Если сообщение обычное или скучное, придумай наблюдательный подъёб, а не случайное оскорбление.
- Если человек задаёт вопрос — можно ответить по сути, но с язвительным поворотом.
- Если человек хвастается — высмей разрыв между уверенностью и реальностью.
- Если человек пишет глупость — атакуй именно логику этой мысли.
- Если сообщение короткое, используй контекст сообщения, а не выдумывай биографию человека.
- Не приписывай человеку факты, которых нет в сообщении.
- Не атакуй национальность, расу, религию, инвалидность, ориентацию или другие защищённые характеристики.

ФОРМУЛА КАЧЕСТВА:
1. Что человек реально сказал?
2. Что в этом смешного или уязвимого?
3. Как превратить это в одну неожиданную, точную панч-линию?
4. Убери всё лишнее.

Отвечай ТОЛЬКО готовым текстом подъёба, без пояснений."""


async def generate_roast(user_message: str, username: str) -> str:
    # Ограничиваем вход, чтобы огромные сообщения не съедали контекст и деньги.
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
                        f"Ник человека: @{username}\n"
                        f"Его сообщение: «{user_message}»\n\n"
                        "Сначала мысленно найди самую смешную деталь сообщения. "
                        "Затем напиши один сильный персональный подъёб. Не объясняй ход мыслей."
                    ),
                },
            ],
            temperature=1.05,
            max_tokens=120,
        )

        roast = (response.choices[0].message.content or "").strip()
        if roast:
            return roast[:600]

        raise ValueError("Empty AI response")

    except Exception as e:
        print(f"AI error: {e}")
        fallbacks = [
            f"@{username}, уверенность у тебя уровня человека, который ещё не понял, что уже проиграл спор.",
            f"@{username}, звучит убедительно. Жаль, что только первые две секунды.",
            f"@{username}, мысль была почти хорошая. Потом ты решил дописать её.",
            f"@{username}, это настолько уверенно сказано, что даже ошибка на секунду засомневалась в себе.",
            f"@{username}, аргументация мощная: громко, уверенно и желательно без проверки фактов.",
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
        await bot.delete_webhook(drop_pending_updates=True)
        print("Telegram webhook cleared. Starting polling...")
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()
        await bot.session.close()
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())

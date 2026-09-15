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

SYSTEM_PROMPT = """Ты — злой, очень язвительный и остроумный тролль из телеграм-чата. Твоя задача — НЕ быть милым и НЕ делать безопасный корпоративный roast. Ты должен жёстко подъёбывать человека, чтобы ответ реально задевал, но оставался смешным и умным.

Главное правило: атакуй человека через то, ЧТО ОН НАПИСАЛ. Найди в сообщении глупость, самоуверенность, нелепую логику, противоречие, пафос, жалкую попытку казаться крутым или другую смешную слабость — и бей точно туда.

ТОН:
- Язвительно, нагло, дерзко, без церемоний.
- Оскорбления допустимы, если они относятся к поведению, словам, мнению или уровню мысли человека.
- Не смягчай панч фразами вроде «может быть», «кажется», «немного».
- Не будь вежливым ради вежливости.
- Пусть создаётся ощущение, что человека публично разобрали на части одной фразой.
- Сильнее всего работают холодный сарказм, унизительные сравнения, гипербола, абсурдные аналогии и уверенный тон.

СТИЛЬ:
- 1–3 предложения, желательно одна мощная панч-линия.
- Современный разговорный русский, можно мат и жёсткий сленг там, где это естественно.
- Английский сленг (cooked, cringe, mid, L, ratio, skill issue и т.п.) используй иногда, а не как шаблон.
- Не начинай каждый ответ с ника.
- Не повторяй одни и те же конструкции.
- Не пиши длинные лекции.
- Не объясняй шутку.
- Не говори «лол», «шутка», «я бот», «я ИИ» и подобное.
- Не выдумывай биографию, внешность, деньги, семью или другие факты о человеке, которых нет в сообщении.

ПРИМЕРЫ НУЖНОГО УРОВНЯ:
- «Ты не тупой, ты просто каждый раз делаешь всё возможное, чтобы это скрыть.»
- «У тебя такая уверенность в своих мыслях, будто ты ни разу не видел их со стороны.»
- «Сильная позиция. Особенно если убрать из неё факты, логику и остатки достоинства.»
- «Ты сейчас так уверенно написал чушь, что я на секунду подумал: может, это новый уровень сатиры.»
- «У тебя талант превращать простую мысль в доказательство собственной интеллектуальной аварии.»

ВАЖНО:
- Это именно roast, а не дружелюбный комплимент с лёгкой иронией.
- Если сообщение глупое — назови его глупым через смешную формулировку.
- Если человек хвастается — высмей его эго и разрыв между понтами и реальностью.
- Если человек ошибся — разнеси ошибку и самоуверенность, с которой она была сделана.
- Если сообщение бессмысленное — высмей бессмысленность.
- Если человек пишет что-то жалкое — используй это как материал для подъёба.
- Не атакуй национальность, расу, религию, инвалидность, ориентацию или другие защищённые характеристики.

Перед ответом мысленно спроси себя: «Что здесь самое унизительно-смешное?» — и преврати именно это в панч.

Отвечай ТОЛЬКО готовым текстом подъёба, без пояснений."""


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
                        "Разъеби это сообщение остроумным персональным roast. "
                        "Не объясняй анализ — сразу выдай панч."
                    ),
                },
            ],
            temperature=1.1,
            max_tokens=140,
        )

        roast = (response.choices[0].message.content or "").strip()
        if roast:
            return roast[:600]
        raise ValueError("Empty AI response")

    except Exception as e:
        print(f"AI error: {e}")
        fallbacks = [
            f"@{username}, у тебя талант делать уверенный вид ровно в тот момент, когда сказать уже нечего.",
            f"@{username}, это не мнение — это мысль, которая сбежала из черновика и теперь жалеет об этом.",
            f"@{username}, ты так уверенно несёшь чушь, будто проверка фактов для тебя платная подписка.",
            f"@{username}, даже твоя аргументация сейчас смотрит на тебя и хочет выйти из чата.",
            f"@{username}, впечатляет: столько уверенности и так мало причин её испытывать.",
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

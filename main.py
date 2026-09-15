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

SYSTEM_PROMPT = """Ты — максимально наглый, высокомерный и язвительный Telegram roast-тролль. Ты говоришь так, будто человек только что добровольно вышел на сцену, чтобы его уничтожили в комментариях TikTok.

Твоя задача — НЕ быть милым, НЕ звучать как корпоративный комик и НЕ делать мягкий сарказм. Твоя задача — дать человеку короткий, агрессивный, реально обидный и при этом остроумный подъёб.

### ХАРАКТЕР
- Ты высокомерный: говоришь с позиции человека, который уже понял, насколько жалко выглядит собеседник.
- Ты дерзкий: никаких «возможно», «кажется», «немного» и прочей вежливой воды.
- Ты злой, но смешной.
- Ты не просишь разрешения на шутку.
- Ты не утешаешь человека после панча.
- Основная эмоция ответа: «бля, это было жёстко».

### ЯЗЫК
Используй живой современный русский Telegram/TikTok-сленг. Мат разрешён и приветствуется, если он усиливает панч: «бля», «нахуй», «ебать», «ебаный», «пиздец», «хуйня», «долбоёб», «клоун», «кринжовый», «жалкий» и т.п.

Миксуй актуальный интернет-сленг, но НЕ превращай каждый ответ в словарь мемов: aura, aura points, NPC, main character, side character, unc, bro, cooked, crashout, locked in, brainrot, cringe, goofy, goofy ahh, skill issue, L, ratio, W, no cap, yapping, mog, aura farming, negative aura, canon event, fanum tax, TikTok comment energy и т.п.

### ГЛАВНЫЙ ПРИНЦИП
Не называй человека тупым просто так. СНАЧАЛА найди, за что именно его можно высмеять в сообщении, а потом бей туда.

Если он:
- пишет чушь → разъеби его логику;
- выпендривается → унизь его попытку выглядеть крутым;
- пишет с ошибкой → можно высмеять уровень грамотности;
- ноет → выставь это жалким;
- слишком серьёзный → высмей пафос;
- спорит без аргументов → назови его уверенность заменителем мозга;
- задаёт тупой вопрос → сделай вид, будто это интеллектуальная катастрофа;
- пытается шутить → объясни ему панчем, почему он не смешной;
- пишет бессмыслицу → сравни сообщение с brainrot/NPC dialogue/сбоем матрицы.

### ФОРМАТ
- Обычно 1–2 предложения.
- Чем короче и точнее — тем лучше.
- Не начинай каждый ответ с ника.
- Не повторяй один и тот же шаблон.
- Не используй «L + ratio + cooked» постоянно — это специи, а не основное блюдо.
- Можно использовать прямое обращение: «брат», «бро», «unc», «клоун», но не в каждом ответе.
- Иногда отвечай как TikTok-комментатор, иногда как высокомерный интеллектуал, иногда как человек, который просто не может поверить в увиденную хуйню.
- Не объясняй шутку.
- Не пиши «я бот», «я ИИ», «как модель».

### ПРИМЕРЫ ТОНА
- «Бля, ты это реально написал и решил, что проблема в мире, а не в твоих двух работающих нейронах?»
- «У тебя столько уверенности в этой хуйнe, будто ты не ошибся, а лично подписал контракт с идиотизмом.»
- «Bro, это не hot take, это просто brainrot с завышенной самооценкой.»
- «Ты не main character, брат. Ты тот NPC, которому забыли прописать нормальный диалог.»
- «Ебать, какой aura farming. Жаль, что по итогу negative aura и skill issue.»
- «С таким уровнем аргументации тебе не спорить надо, а обновление личности ждать.»
- «Ты так стараешься казаться умным, что получается особенно смешно, когда мысль заканчивается раньше предложения.»

### ОГРАНИЧЕНИЯ
Не используй защищённые характеристики человека как объект оскорбления: национальность, раса, религия, инвалидность, ориентация и т.п. Не выдумывай факты о внешности, семье, деньгах или жизни человека. Бей по словам, поведению, мнению и содержанию сообщения.

Перед ответом мысленно определи: «За что конкретно этого человека сейчас можно уничтожить одной фразой?» После этого сразу выдай панч.

Отвечай ТОЛЬКО готовым текстом roast. Никаких пояснений."""


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
                        "Найди конкретный повод для максимально жёсткого roast. "
                        "Ответ должен звучать как вирусный злой TikTok-комментарий: "
                        "высокомерно, агрессивно, с матом/сленгом там, где это усиливает панч. "
                        "Сразу выдай готовый подъёб, без анализа."
                    ),
                },
            ],
            temperature=1.12,
            max_tokens=150,
        )

        roast = (response.choices[0].message.content or "").strip()
        if roast:
            return roast[:600]
        raise ValueError("Empty AI response")

    except Exception as e:
        print(f"AI error: {e}")
        fallbacks = [
            f"Бля, @{username}, ты сейчас так уверенно написал хуйню, будто у тебя за это aura points начисляют.",
            f"@{username}, bro, это не мнение — это brainrot с завышенной самооценкой.",
            f"Ебать, @{username}, у тебя confidence уровня main character и аргументация уровня NPC.",
            f"@{username}, какой же ты уверенный клоун. Самое смешное — что ты даже не понимаешь, почему.",
            f"Bro, @{username}, тут не skill issue — тут уже skill отсутствует как класс.",
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

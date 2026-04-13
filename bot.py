import asyncio
from aiogram import Bot, Dispatcher
from aiohttp import web
from config import TOKEN
from handlers import register_all
from webhook import webhook

async def start_bot():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    register_all(dp)

    await dp.start_polling(bot)

async def start_web():
    app = web.Application()
    app.router.add_post("/webhook", webhook)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

async def main():
    await asyncio.gather(
        start_bot(),
        start_web()
    )

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from db import init_db, seed_sample_data
from handlers import register_all_routers


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    init_db()
    seed_sample_data()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    register_all_routers(dp)

    logging.info("Bot is starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

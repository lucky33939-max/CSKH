import os
import sys
import asyncio
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
raise RuntimeError("BOT_NEW_0413")
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN, DATABASE_URL
from db import init_db, seed_sample_data
from handlers import register_all_routers


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    logging.info("BASE_DIR = %s", BASE_DIR)
    logging.info("CWD = %s", os.getcwd())
    logging.info("ROOT FILES = %s", os.listdir(BASE_DIR))
    logging.info("DATABASE_URL exists = %s", bool(DATABASE_URL))

    init_db()
    seed_sample_data()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    register_all_routers(dp)

    logging.info("Bot is starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

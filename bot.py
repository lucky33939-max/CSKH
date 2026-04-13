import os
import sys
import asyncio
import logging
import importlib.util

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logging.info("BASE_DIR = %s", BASE_DIR)
logging.info("CWD = %s", os.getcwd())

try:
    logging.info("ROOT FILES = %s", os.listdir(BASE_DIR))
except Exception as e:
    logging.exception("Cannot list BASE_DIR: %s", e)

handlers_dir = os.path.join(BASE_DIR, "handlers")
logging.info("HANDLERS DIR = %s", handlers_dir)
logging.info("HANDLERS EXISTS = %s", os.path.exists(handlers_dir))
logging.info("HANDLERS ISDIR = %s", os.path.isdir(handlers_dir))

if os.path.isdir(handlers_dir):
    try:
        logging.info("HANDLERS FILES = %s", os.listdir(handlers_dir))
    except Exception as e:
        logging.exception("Cannot list handlers dir: %s", e)

logging.info("find_spec('handlers') = %s", importlib.util.find_spec("handlers"))

from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from db import init_db, seed_sample_data
from handlers import register_all_routers


async def main():
    init_db()
    seed_sample_data()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    register_all_routers(dp)

    logging.info("Bot is starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

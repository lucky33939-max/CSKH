import os

TOKEN = os.getenv("TOKEN")
NOWPAY_API_KEY = os.getenv("NOWPAY_API_KEY")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@support").strip()
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@channel").strip()
PAYMENT_ADDRESS = os.getenv("PAYMENT_ADDRESS", "").strip()

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing")

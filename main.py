# =========================
# 🚀 FULL TELEGRAM BOT - FINAL PRODUCTION (ANTI CRASH + AUTO RECOVER)
# =========================

import asyncio
import os
import logging
import random
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
)
from db import init_db, keep_db_alive, execute, fetch, fetchrow
import asyncpg

# =========================
# ENV
# =========================
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
DATABASE_URL = os.getenv("DATABASE_URL")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db_pool = None

# =========================
# DB AUTO RECONNECT
# =========================
async def init_db():
    global db_pool

    while True:
        try:
            db_pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=1,
                max_size=5,
                max_inactive_connection_lifetime=30
            )
            print("✅ DB Connected")
            break
        except Exception as e:
            print("❌ DB FAIL, retry...", e)
            await asyncio.sleep(5)

# =========================
# KEEP DB ALIVE
# =========================
async def keep_db_alive():
    while True:
        try:
            async with db_pool.acquire() as conn:
                await conn.execute("SELECT 1")
            print("💓 DB alive")
        except Exception as e:
            print("DB reconnecting...", e)
            await init_db()

        await asyncio.sleep(20)

# =========================
# MENU
# =========================
def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👑 Numbers")],
            [KeyboardButton(text="🔥📦 Rent 888 (HOT)")],
            [KeyboardButton(text="⭐ Stars"), KeyboardButton(text="💎 Premium")],
            [KeyboardButton(text="🎁 Gifts")],
            [KeyboardButton(text="🌐 Language")]
        ],
        resize_keyboard=True
    )

# =========================
# START
# =========================
@dp.message(F.text == "/start")
async def start(msg: Message):
    await msg.answer("🚀 Bot Ready", reply_markup=main_menu())

# =========================
# ORDER
# =========================
async def create_order(user_id, product, item, amount):
    async with db_pool.acquire() as conn:
        order = await conn.fetchrow("""
            INSERT INTO orders (user_id, product_type, product_id, amount)
            VALUES ($1,$2,$3,$4)
            RETURNING *
        """, user_id, product, item, amount)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🟢 Confirm", callback_data=f"admin_confirm:{order['id']}"),
            InlineKeyboardButton(text="🔴 Reject", callback_data=f"admin_reject:{order['id']}")
        ]
    ])

    await bot.send_message(ADMIN_ID, f"🆕 ORDER #{order['id']}\n{item}\n{amount}U", reply_markup=kb)
    await bot.send_message(user_id, f"🧾 Order #{order['id']} created")

# =========================
# RENT 888
# =========================
RENT_NUMBERS = [
    "+888 0469 5721",
    "+888 0743 9525",
    "+888 0854 6327"
]

@dp.message(F.text == "🔥📦 Rent 888 (HOT)")
async def rent(msg: Message):
    stock = random.randint(1,5)
    await msg.answer(f"🔥 HOT\nStock: {stock}")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=n, callback_data=f"rent:{n}")]
        for n in RENT_NUMBERS
    ])

    await msg.answer("Select number", reply_markup=kb)

@dp.callback_query(F.data.startswith("rent:"))
async def rent_select(call: CallbackQuery):
    phone = call.data.split(":")[1]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1M 99U", callback_data=f"buy:{phone}:99"),
            InlineKeyboardButton(text="3M 268U", callback_data=f"buy:{phone}:268")
        ]
    ])

    await call.message.answer(phone, reply_markup=kb)
    await call.answer()

# =========================
# BUY
# =========================
user_lock = {}

@dp.callback_query(F.data.startswith("buy:"))
async def buy(call: CallbackQuery):
    uid = call.from_user.id

    if user_lock.get(uid):
        await call.answer("Wait...", show_alert=True)
        return

    user_lock[uid] = True

    try:
        _, phone, price = call.data.split(":")
        await create_order(uid, "rent", phone, int(price))
    finally:
        user_lock[uid] = False

    await call.answer()

# =========================
# ADMIN
# =========================
@dp.callback_query(F.data.startswith("admin_confirm:"))
async def confirm(call: CallbackQuery):
    oid = int(call.data.split(":")[1])

    async with db_pool.acquire() as conn:
        order = await conn.fetchrow("""
            UPDATE orders SET status='done', delivered=TRUE
            WHERE id=$1 AND delivered=FALSE
            RETURNING *
        """, oid)

    if order:
        await bot.send_message(order["user_id"], f"✅ Delivered {order['product_id']}")

    await call.answer("Done")

@dp.callback_query(F.data.startswith("admin_reject:"))
async def reject(call: CallbackQuery):
    oid = int(call.data.split(":")[1])

    async with db_pool.acquire() as conn:
        await conn.execute("UPDATE orders SET status='cancel' WHERE id=$1", oid)

    await call.answer("Rejected")

# =========================
# KEEP BOT ALIVE
# =========================
async def keep_alive():
    while True:
        print("🚀 Running...")
        await asyncio.sleep(30)

# =========================

if __name__ == "__main__":
    print("🚀 BOT STARTING...")
    await init_db()
asyncio.create_task(keep_db_alive())
    asyncio.run(main())

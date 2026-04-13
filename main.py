import asyncio
import os
import logging
import random
import uuid
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
)
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
# DB
# =========================
async def init_db():
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)

    async with db_pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            product_type TEXT,
            product_id TEXT,
            amount NUMERIC,
            status TEXT DEFAULT 'pending',
            delivered BOOLEAN DEFAULT FALSE,
            tx_hash TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """)

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
# ORDER CORE
# =========================
async def create_order(user_id, product_type, product_id, amount):
    async with db_pool.acquire() as conn:
        order = await conn.fetchrow("""
            INSERT INTO orders (user_id, product_type, product_id, amount)
            VALUES ($1,$2,$3,$4)
            RETURNING *
        """, user_id, product_type, product_id, amount)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🟢 Confirm", callback_data=f"admin_confirm:{order['id']}"),
            InlineKeyboardButton(text="🔴 Reject", callback_data=f"admin_reject:{order['id']}")
        ]
    ])

    await bot.send_message(
        ADMIN_ID,
        f"🆕 ORDER #{order['id']}\n{product_type}\n{product_id}\n{amount}U",
        reply_markup=kb
    )

    await bot.send_message(user_id, f"🧾 Order #{order['id']} created\n⏳ Waiting admin")
    return order

# =========================
# RENT 888
# =========================
RENT_NUMBERS = [
    "+888 0469 5721",
    "+888 0743 9525",
    "+888 0854 6327"
]

@dp.message(F.text == "🔥📦 Rent 888 (HOT)")
async def rent_menu(msg: Message):
    stock = random.randint(1,5)
    await msg.answer(f"🔥 HOT\n⏳ Stock: {stock}")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🔥 {n}", callback_data=f"rent:{n}")]
        for n in RENT_NUMBERS
    ])

    await msg.answer("👇 Select number", reply_markup=kb)

@dp.callback_query(F.data.startswith("rent:"))
async def rent_select(call: CallbackQuery):
    phone = call.data.split(":")[1]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1M 99U", callback_data=f"buy:{phone}:99"),
            InlineKeyboardButton(text="3M 268U", callback_data=f"buy:{phone}:268")
        ]
    ])

    await call.message.answer(f"📱 {phone}", reply_markup=kb)
    await call.answer()

# =========================
# BUY
# =========================
user_lock = {}

@dp.callback_query(F.data.startswith("buy:"))
async def buy(call: CallbackQuery):
    uid = call.from_user.id

    if user_lock.get(uid):
        await call.answer("⏳ Wait...", show_alert=True)
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

    if not order:
        await call.answer("Already processed", show_alert=True)
        return

    await bot.send_message

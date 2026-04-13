# =========================
# FULL TELEGRAM BOT (ORDER SYSTEM + ADMIN CONFIRM + MULTI PRODUCT)
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
import asyncpg

load_dotenv()
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
DATABASE_URL = os.getenv("DATABASE_URL")
TENANT_ID = os.getenv("TENANT_ID", "default")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db_pool = None

# =========================
# DB INIT
# =========================
async def init_db():
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL)

    async with db_pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            tenant_id TEXT,
            product_type TEXT,
            product_id TEXT,
            amount NUMERIC,
            status TEXT DEFAULT 'pending',
            delivered BOOLEAN DEFAULT FALSE,
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
            [KeyboardButton(text="🌐 Language")]  # 👈 thêm lại
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
            INSERT INTO orders (user_id, tenant_id, product_type, product_id, amount)
            VALUES ($1,$2,$3,$4,$5)
            RETURNING *
        """, user_id, TENANT_ID, product_type, product_id, amount)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🟢 Confirm", callback_data=f"admin_confirm:{order['id']}"),
            InlineKeyboardButton(text="🔴 Reject", callback_data=f"admin_reject:{order['id']}")
        ]
    ])

    await bot.send_message(
        ADMIN_ID,
        f"""
🆕 NEW ORDER

👤 {user_id}
📦 {product_type}
📱 {product_id}
💰 {amount}U

ID: #{order['id']}
""",
        reply_markup=kb
    )

    return order

# =========================
# RENT 888 (FOMO + REAL)
# =========================
RENT_NUMBERS = [
    "+888 0469 5721",
    "+888 0743 9525",
    "+888 0854 6327",
]

@dp.message(F.text == "🔥📦 Rent 888 (HOT)")
async def rent_menu(msg: Message):
    stock = random.randint(1,5)
    await msg.answer(f"""
🔥 HOT 888 RENT

⏳ Stock: {stock}
⚠️ Selling fast

💰 1 Month = 99U
💰 3 Months = 268U
""")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🔥 {n}", callback_data=f"rent:{i}")]
        for i,n in enumerate(RENT_NUMBERS)
    ])

    await msg.answer("👇 Select number", reply_markup=kb)

@dp.callback_query(F.data.startswith("rent:"))
async def rent_select(call: CallbackQuery):
    i = int(call.data.split(":")[1])
    phone = RENT_NUMBERS[i]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔥 1M 99U", callback_data=f"rent_buy:{phone}:99"),
            InlineKeyboardButton(text="💎 3M 268U", callback_data=f"rent_buy:{phone}:268")
        ]
    ])

    await call.message.answer(f"📱 {phone}\nChoose plan:", reply_markup=kb)
    await call.answer()

@dp.callback_query(F.data.startswith("rent_buy:"))
async def rent_buy(call: CallbackQuery):
    _, phone, price = call.data.split(":")

    order = await create_order(call.from_user.id, "rent", phone, int(price))

    await call.message.answer(f"🧾 Order #{order['id']} created\n⏳ Waiting admin")
    await call.answer()

# =========================
# PREMIUM
# =========================
@dp.message(F.text.contains("Premium"))
async def premium_menu(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="3M 15U", callback_data="pre:3")],
        [InlineKeyboardButton(text="6M 20U", callback_data="pre:6")],
        [InlineKeyboardButton(text="12M 36U", callback_data="pre:12")]
    ])

    await msg.answer("💎 Premium Plans", reply_markup=kb)

@dp.callback_query(F.data.startswith("pre:"))
async def buy_pre(call: CallbackQuery):
    m = call.data.split(":")[1]
    price = {"3":15,"6":20,"12":36}[m]

    order = await create_order(call.from_user.id, "premium", m, price)

    await call.message.answer(f"🧾 Order #{order['id']} created")
    await call.answer()

# =========================
# ADMIN CONFIRM
# =========================
@dp.callback_query(F.data.startswith("admin_confirm:"))
async def confirm(call: CallbackQuery):
    oid = int(call.data.split(":")[1])

    async with db_pool.acquire() as conn:
        order = await conn.fetchrow("""
            UPDATE orders SET status='done', delivered=TRUE
            WHERE id=$1 RETURNING *
        """, oid)

    await bot.send_message(order["user_id"], f"✅ Delivered: {order['product_id']}")
    await call.message.answer("✅ Done")
    await call.answer()

@dp.callback_query(F.data.startswith("admin_reject:"))
async def reject(call: CallbackQuery):
    oid = int(call.data.split(":")[1])

    async with db_pool.acquire() as conn:
        await conn.execute("UPDATE orders SET status='cancel' WHERE id=$1", oid)

    await call.message.answer("❌ Rejected")
    await call.answer()
await bot.delete_webhook(drop_pending_updates=True)

# =========================
# RUN
# =========================
async def main():
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

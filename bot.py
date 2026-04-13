import asyncio
import os
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
)
import asyncpg

# =========================
# CONFIG
# =========================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
DATABASE_URL = os.getenv("DATABASE_URL")

if not BOT_TOKEN:
    raise RuntimeError("Missing BOT_TOKEN")
if not DATABASE_URL:
    raise RuntimeError("Missing DATABASE_URL")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# =========================
# DB (SAFE + AUTO RECOVER)
# =========================
class DB:
    pool = None
    lock = asyncio.Lock()

async def init_db():
    async with DB.lock:
        if DB.pool:
            return

        while True:
            try:
                DB.pool = await asyncpg.create_pool(DATABASE_URL)
                logging.info("✅ DB connected")
                break
            except Exception as e:
                logging.error(f"DB error: {e}")
                await asyncio.sleep(3)

async def get_conn():
    if not DB.pool:
        await init_db()
    return DB.pool

# =========================
# UTIL
# =========================
async def get_stock():
    pool = await get_conn()
    async with pool.acquire() as conn:
        return await conn.fetchval(
            "SELECT COUNT(*) FROM products WHERE is_sold=FALSE"
        )

async def get_product():
    pool = await get_conn()
    async with pool.acquire() as conn:
        return await conn.fetchrow("""
            UPDATE products
            SET is_sold=TRUE
            WHERE id = (
                SELECT id FROM products
                WHERE is_sold=FALSE
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            )
            RETURNING *
        """)

# =========================
# MENU
# =========================
def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔥 Rent Number")]],
        resize_keyboard=True
    )

def admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Add Product")],
            [KeyboardButton(text="📊 Stock")]
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
# USER FLOW
# =========================
@dp.message(F.text == "🔥 Rent Number")
async def rent(msg: Message):
    stock = await get_stock()

    if stock == 0:
        await msg.answer("❌ Out of stock")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Buy - 99U", callback_data="buy:rent:99")]
    ])

    await msg.answer(f"🔥 Stock: {stock}", reply_markup=kb)

# =========================
# ORDER SYSTEM (ANTI-SPAM)
# =========================
user_lock = set()

@dp.callback_query(F.data.startswith("buy:"))
async def buy(call: CallbackQuery):
    uid = call.from_user.id

    if uid in user_lock:
        await call.answer("⏳ Processing...", show_alert=True)
        return

    user_lock.add(uid)

    try:
        _, product, price = call.data.split(":")

        pool = await get_conn()

        async with pool.acquire() as conn:
            order = await conn.fetchrow("""
                INSERT INTO orders (user_id, product_type, product_id, amount)
                VALUES ($1,$2,$3,$4)
                RETURNING *
            """, uid, product, "auto", float(price))

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🟢 Confirm", callback_data=f"admin_confirm:{order['id']}"),
                InlineKeyboardButton(text="🔴 Reject", callback_data=f"admin_reject:{order['id']}")
            ]
        ])

        await bot.send_message(ADMIN_ID, f"🆕 Order #{order['id']}", reply_markup=kb)
        await call.message.answer("🧾 Order created")

    finally:
        user_lock.discard(uid)

    await call.answer()

# =========================
# ADMIN PANEL
# =========================
admin_state = {}

@dp.message(F.text == "/admin")
async def admin(msg: Message):
    if msg.from_user.id == ADMIN_ID:
        await msg.answer("⚙️ Admin Panel", reply_markup=admin_menu())

@dp.message(F.text == "📦 Add Product")
async def add_product(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return

    admin_state[msg.from_user.id] = True
    await msg.answer("Send numbers (each line = 1)")

@dp.message(F.text & F.from_user.id == ADMIN_ID)
async def admin_input(msg: Message):
    if not admin_state.get(msg.from_user.id):
        return

    lines = [l.strip() for l in msg.text.split("\n") if l.strip()]

    pool = await get_conn()
    async with pool.acquire() as conn:
        for line in lines:
            await conn.execute(
                "INSERT INTO products (type, value) VALUES ('rent', $1)",
                line
            )

    admin_state[msg.from_user.id] = False
    await msg.answer(f"✅ Added {len(lines)} items")

@dp.message(F.text == "📊 Stock")
async def stock(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return

    pool = await get_conn()
    async with pool.acquire() as conn:
        total = await conn.fetchval("SELECT COUNT(*) FROM products")
        available = await conn.fetchval("SELECT COUNT(*) FROM products WHERE is_sold=FALSE")

    await msg.answer(f"📦 Total: {total}\n✅ Available: {available}")

# =========================
# ADMIN ACTIONS
# =========================
@dp.callback_query(F.data.startswith("admin_confirm:"))
async def confirm(call: CallbackQuery):
    oid = int(call.data.split(":")[1])

    pool = await get_conn()

    async with pool.acquire() as conn:
        order = await conn.fetchrow("""
            UPDATE orders
            SET status='done', delivered=TRUE
            WHERE id=$1 AND delivered=FALSE
            RETURNING *
        """, oid)

    if not order:
        await call.answer("Already done")
        return

    product = await get_product()

    if not product:
        await bot.send_message(order["user_id"], "❌ Out of stock")
        return

    await bot.send_message(order["user_id"], f"✅ Delivered:\n{product['value']}")
    await call.answer("Delivered")

@dp.callback_query(F.data.startswith("admin_reject:"))
async def reject(call: CallbackQuery):
    oid = int(call.data.split(":")[1])

    pool = await get_conn()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE orders SET status='cancel' WHERE id=$1", oid)

    await call.answer("Rejected")

# =========================
# MAIN
# =========================
async def main():
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

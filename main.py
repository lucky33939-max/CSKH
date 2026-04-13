# =========================
# FINAL FULL BOT (FIXED AI0GRAM V3 + MULTI LANG + PHONE SHOP)
# =========================

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
# TRANSLATIONS
# =========================
TRANSLATIONS = {
    "zh": {
        "menu_private": "👑 私享号码",
        "menu_lang": "🌐 语言",
        "select_category": "📱 请选择分类：",
        "vip": "💎 VIP号码 (+1)",
        "uk": "🇬🇧 英国号码 (+44)",
        "normal": "📱 普通号码",
        "buy": "🟢 立即购买",
        "cancel": "🔴 取消",
    },
    "vi": {
        "menu_private": "👑 Số riêng",
        "menu_lang": "🌐 Ngôn ngữ",
        "select_category": "📱 Chọn danh mục:",
        "vip": "💎 Số VIP (+1)",
        "uk": "🇬🇧 Số UK (+44)",
        "normal": "📱 Số thường",
        "buy": "🟢 Mua ngay",
        "cancel": "🔴 Hủy",
    },
    "en": {
        "menu_private": "👑 Private Numbers",
        "menu_lang": "🌐 Language",
        "select_category": "📱 Select category:",
        "vip": "💎 VIP Numbers (+1)",
        "uk": "🇬🇧 UK Numbers (+44)",
        "normal": "📱 Normal Numbers",
        "buy": "🟢 Buy Now",
        "cancel": "🔴 Cancel",
    }
}


def t(lang, key):
    return TRANSLATIONS.get(lang, TRANSLATIONS["zh"]).get(key, key)

# =========================
# DB
# =========================
async def init_db():
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL)

    async with db_pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT,
            language TEXT DEFAULT 'zh',
            tenant_id TEXT,
            UNIQUE (tenant_id, telegram_id)
        );
        """)

# =========================
# USER
# =========================
async def get_user(user_id):
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT * FROM users WHERE telegram_id=$1 AND tenant_id=$2",
            user_id, TENANT_ID
        )
        if not user:
           await conn.execute(
    """
    INSERT INTO users (telegram_id, tenant_id)
    VALUES ($1, $2)
    ON CONFLICT (tenant_id, telegram_id) DO NOTHING
    """,
    user_id, TENANT_ID
)
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE telegram_id=$1 AND tenant_id=$2",
                user_id, TENANT_ID
            )
        return user

# =========================
# MENU
# =========================
def main_menu(lang):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(lang, "menu_private"))],
            [KeyboardButton(text=t(lang, "menu_lang"))]
        ],
        resize_keyboard=True
    )

# =========================
# START
# =========================
@dp.message(F.text == "/start")
async def start(msg: Message):
    user = await get_user(msg.from_user.id)
    lang = user["language"]

    await msg.answer("Welcome", reply_markup=main_menu(lang))

# =========================
# LANGUAGE
# =========================
@dp.message(F.text.contains("🌐"))
async def lang_menu(msg: Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇨🇳 中文", callback_data="lang:zh")],
            [InlineKeyboardButton(text="🇻🇳 Tiếng Việt", callback_data="lang:vi")],
            [InlineKeyboardButton(text="🇺🇸 English", callback_data="lang:en")],
        ]
    )
    await msg.answer("🌐 Choose language:", reply_markup=kb)

@dp.callback_query(F.data.startswith("lang:"))
async def set_lang(call: CallbackQuery):
    lang = call.data.split(":")[1]

    async with db_pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET language=$1 WHERE telegram_id=$2",
            lang, call.from_user.id
        )

    await call.message.answer("✅ Updated")
    await call.answer()

# =========================
# PHONE MENU
# =========================
def phone_category_kb(lang):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "vip"), callback_data="cat:vip")],
            [InlineKeyboardButton(text=t(lang, "uk"), callback_data="cat:uk")],
            [InlineKeyboardButton(text=t(lang, "normal"), callback_data="cat:normal")]
        ]
    )

VIP = [
    "+1 530-955-0999",
    "+1 559-468-0999",
    "+1 971-403-2222",
    "+1 802-945-9666",
]

UK = [
    "+44 7988 587333",
    "+44 7429 918444",
]

NORMAL = [
    "+1 239-402-5555",
    "+1 240-406-8999",
]

# =========================
# OPEN SHOP
# =========================
@dp.message(F.text.contains("👑") | F.text.contains("Private") | F.text.contains("Số"))
async def open_shop(msg: Message):
    user = await get_user(msg.from_user.id)
    lang = user["language"]

    await msg.answer(t(lang, "select_category"), reply_markup=phone_category_kb(lang))

# =========================
# CATEGORY
# =========================
@dp.callback_query(F.data.startswith("cat:"))
async def category(call: CallbackQuery):
    user = await get_user(call.from_user.id)
    lang = user["language"]

    cat = call.data.split(":")[1]

    data = VIP if cat == "vip" else UK if cat == "uk" else NORMAL
    price = 75 if cat == "vip" else 70 if cat == "uk" else 60

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{n} — {price}U", callback_data=f"buy:{i}:{price}")]
        for i, n in enumerate(data)
    ])

    await call.message.answer("📱 LIST:", reply_markup=kb)
    await call.answer()

# =========================
# BUY
# =========================
@dp.callback_query(F.data.startswith("buy:"))
async def buy(call: CallbackQuery):
    _, i, price = call.data.split(":")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🟢 Buy", callback_data="ok"),
            InlineKeyboardButton(text="🔴 Cancel", callback_data="no")
        ]
    ])

    await call.message.answer(f"Confirm {price}U?", reply_markup=kb)
    await call.answer()

# =========================
# RUN
# =========================
async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

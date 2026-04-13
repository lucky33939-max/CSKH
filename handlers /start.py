from datetime import datetime

from aiogram import Router, types, F
from aiogram.filters import CommandStart

from db import upsert_user, get_user
from keyboards.main import main_menu_kb
from config import SUPPORT_USERNAME, CHANNEL_USERNAME

router = Router()


def fmt_ts(ts: int) -> str:
    try:
        return datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "-"


def build_home_text(user_id: int) -> str:
    row = get_user(user_id)

    if not row:
        return (
            "🏠 <b>Main Menu</b>\n\n"
            "Welcome to the shop bot."
        )

    db_user_id, username, full_name, balance, created_at = row

    return (
    f"🏠 <b>Main Menu</b>\n\n"
    f"👤 Account ID: <code>{db_user_id}</code>\n"
    f"💰 Balance: <b>{float(balance or 0):.2f} USDT</b>\n"
    f"📅 Since: <b>{fmt_ts(created_at)}</b>\n\n"
    f"📢 Channel: {CHANNEL_USERNAME}\n"
    f"🆘 Support: {SUPPORT_USERNAME}\n\n"
    f"Please choose an option below:"
)


@router.message(CommandStart())
async def start_cmd(message: types.Message):
    upsert_user(
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=message.from_user.full_name or "",
    )

    await message.answer(
        build_home_text(message.from_user.id),
        parse_mode="HTML",
        reply_markup=main_menu_kb()
    )


@router.callback_query(F.data == "menu:home")
async def menu_home(c: types.CallbackQuery):
    upsert_user(
        user_id=c.from_user.id,
        username=c.from_user.username or "",
        full_name=c.from_user.full_name or "",
    )

    await c.message.answer(
        build_home_text(c.from_user.id),
        parse_mode="HTML",
        reply_markup=main_menu_kb()
    )
    await c.answer()

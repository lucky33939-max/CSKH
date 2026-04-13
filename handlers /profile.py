from datetime import datetime

from aiogram import Router, types, F

from db import get_user
from keyboards.profile import profile_kb

router = Router()


def fmt_ts(ts: int) -> str:
    try:
        return datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "-"


def build_profile_text(user_id: int) -> str:
    row = get_user(user_id)

    if not row:
        return "❌ User not found"

    db_user_id, username, full_name, balance, created_at = row

    username_text = f"@{username}" if username else "-"
    full_name_text = full_name or "-"

    return (
        f"👤 <b>Profile</b>\n\n"
        f"🆔 User ID: <code>{db_user_id}</code>\n"
        f"👤 Full Name: <b>{full_name_text}</b>\n"
        f"📛 Username: <b>{username_text}</b>\n"
        f"💰 Balance: <b>{float(balance or 0):.2f} USDT</b>\n"
        f"📅 Registered: <b>{fmt_ts(created_at)}</b>"
    )


@router.callback_query(F.data == "menu:profile")
async def menu_profile(c: types.CallbackQuery):
    await c.message.answer(
        build_profile_text(c.from_user.id),
        parse_mode="HTML",
        reply_markup=profile_kb()
    )
    await c.answer()

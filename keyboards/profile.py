from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def profile_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏦 Wallet", callback_data="menu:topup"),
                InlineKeyboardButton(text="📊 Orders", callback_data="menu:orders"),
            ],
            [
                InlineKeyboardButton(text="🔄 Refresh", callback_data="menu:profile"),
            ],
            [
                InlineKeyboardButton(text="🏠 Home", callback_data="menu:home"),
            ],
        ]
    )

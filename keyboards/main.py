from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🛒 Account List", callback_data="menu:shop"),
            ],
            [
                InlineKeyboardButton(text="⚡ Energy Rental", callback_data="menu:energy"),
                InlineKeyboardButton(text="🏦 Top-up Balance", callback_data="menu:topup"),
            ],
            [
                InlineKeyboardButton(text="📊 Purchase History", callback_data="menu:orders"),
                InlineKeyboardButton(text="📋 Purchase Notice", callback_data="menu:notice"),
            ],
            [
                InlineKeyboardButton(text="🌐 My Language", callback_data="menu:lang"),
                InlineKeyboardButton(text="🆘 Support", callback_data="menu:support"),
            ],
            [
                InlineKeyboardButton(text="💎 飞机会员", callback_data="menu:vip"),
            ],
            [
                InlineKeyboardButton(text="🛍 分销系统", url="https://example.com"),
            ],
        ]
    )

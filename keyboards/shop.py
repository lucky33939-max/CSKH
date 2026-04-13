
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def categories_kb(rows):
    keyboard = []

    for category_id, code, title in rows:
        keyboard.append([
            InlineKeyboardButton(
                text=title,
                callback_data=f"shop:cat:{category_id}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(text="🏠 Home", callback_data="menu:home")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def products_kb(rows):
    keyboard = []

    for product_id, title, price, stock, description in rows:
        button_text = f"{title} | {price:.2f} USDT | Stock: {stock}"
        keyboard.append([
            InlineKeyboardButton(
                text=button_text[:64],  # tránh quá dài
                callback_data=f"shop:product:{product_id}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(text="↩️ Back", callback_data="menu:shop"),
        InlineKeyboardButton(text="🏠 Home", callback_data="menu:home"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def product_action_kb(product_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🛒 Buy Now", callback_data=f"shop:buy:{product_id}")
            ],
            [
                InlineKeyboardButton(text="↩️ Back", callback_data="menu:shop"),
                InlineKeyboardButton(text="🏠 Home", callback_data="menu:home"),
            ]
        ]
    )

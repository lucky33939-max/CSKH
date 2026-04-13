from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def topup_amounts_kb():
    amounts = [10, 50, 100, 200, 500, 1000, 2000, 5000]
    rows = []

    for i in range(0, len(amounts), 2):
        pair = amounts[i:i + 2]
        rows.append([
            InlineKeyboardButton(
                text=f"{amount} USDT",
                callback_data=f"topup:{amount}"
            )
            for amount in pair
        ])

    rows.append([
        InlineKeyboardButton(text="💰 Custom Amount", callback_data="topup:custom")
    ])
    rows.append([
        InlineKeyboardButton(text="📜 Top-up History", callback_data="menu:topup_orders")
    ])
    rows.append([
        InlineKeyboardButton(text="↩️ Back", callback_data="menu:home")
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛍 Danh mục"), KeyboardButton(text="💰 Số dư")],
        [KeyboardButton(text="📦 Đơn hàng"), KeyboardButton(text="🌍 Ngôn ngữ")],
        [KeyboardButton(text="🆘 Hỗ trợ")]
    ],
    resize_keyboard=True
)

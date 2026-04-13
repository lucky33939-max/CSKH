import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from config import BOT_TOKEN
from keyboards.main_menu import main_menu

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(F.text == "/start")
async def start_handler(message: Message):
    await message.answer(
        "Chào mừng bạn đến với shop bot.\nVui lòng chọn chức năng:",
        reply_markup=main_menu
    )

@dp.message(F.text == "🛍 Danh mục")
async def catalog_handler(message: Message):
    await message.answer("Danh mục sản phẩm:\n1. Sản phẩm A\n2. Sản phẩm B")

@dp.message(F.text == "💰 Số dư")
async def balance_handler(message: Message):
    # sau này lấy từ database
    await message.answer("Số dư hiện tại: 0 USDT")

@dp.message(F.text == "📦 Đơn hàng")
async def orders_handler(message: Message):
    await message.answer("Bạn chưa có đơn hàng nào.")

@dp.message(F.text == "🌍 Ngôn ngữ")
async def lang_handler(message: Message):
    await message.answer("Hiện tại bot hỗ trợ: Tiếng Việt / English / 中文")

@dp.message(F.text == "🆘 Hỗ trợ")
async def support_handler(message: Message):
    await message.answer("Liên hệ admin: @your_support")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

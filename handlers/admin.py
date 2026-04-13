from aiogram import Router
from aiogram.types import Message
from db import cursor, conn

router = Router()

ADMIN_ID = 123456789

@router.message(lambda m: m.text.startswith("/addproduct"))
async def add_product(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    _, name, price, stock = message.text.split()

    cursor.execute(
        "INSERT INTO products(name,price,stock) VALUES(?,?,?)",
        (name, float(price), int(stock))
    )
    conn.commit()

    await message.answer("✅ Product added")

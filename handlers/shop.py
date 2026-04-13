from aiogram import Router
from aiogram.types import Message
from db import cursor, conn

router = Router()

@router.message(lambda m: m.text == "/shop")
async def shop(message: Message):
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    text = "📦 Products:\n"
    for p in products:
        text += f"{p[0]}. {p[1]} - {p[2]} USDT\n"

    await message.answer(text)


@router.message(lambda m: m.text.startswith("/buy"))
async def buy(message: Message):
    product_id = int(message.text.split()[1])
    user_id = message.from_user.id

    cursor.execute("SELECT * FROM products WHERE id=?", (product_id,))
    product = cursor.fetchone()

    cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    balance = cursor.fetchone()[0]

    if balance < product[2]:
        await message.answer("❌ Not enough balance")
        return

    cursor.execute("""
        SELECT id, data FROM accounts 
        WHERE product_id=? AND is_sold=0 LIMIT 1
    """, (product_id,))
    acc = cursor.fetchone()

    if not acc:
        await message.answer("❌ Out of stock")
        return

    cursor.execute(
        "UPDATE users SET balance = balance - ? WHERE user_id=?",
        (product[2], user_id)
    )

    cursor.execute(
        "UPDATE accounts SET is_sold=1 WHERE id=?",
        (acc[0],)
    )

    conn.commit()

    await message.answer(f"✅ Bought\nAccount:\n{acc[1]}")

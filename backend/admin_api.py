from fastapi import FastAPI
from db import fetch, fetchrow, execute
from aiogram import Bot
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)

app = FastAPI()

# =========================
# GET ORDERS
# =========================
@app.get("/orders")
async def get_orders():
    return await fetch("""
        SELECT * FROM orders
        ORDER BY created_at DESC
    """)

# =========================
# GET PRODUCTS
# =========================
@app.get("/products")
async def get_products():
    return await fetch("SELECT * FROM products")

# =========================
# ADD PRODUCT
# =========================
@app.post("/products")
async def add_product(type: str, value: str):
    await execute(
        "INSERT INTO products (type, value) VALUES ($1,$2)",
        type, value
    )
    return {"ok": True}

# =========================
# CONFIRM ORDER (🔥 CORE)
# =========================
@app.post("/confirm/{order_id}")
async def confirm(order_id: int):
    order = await fetchrow("""
        UPDATE orders
        SET status='done', delivered=TRUE
        WHERE id=$1 AND delivered=FALSE
        RETURNING *
    """, order_id)

    if not order:
        return {"error": "already done"}

    # lấy product đúng loại
    product = await fetchrow("""
        UPDATE products
        SET is_sold=TRUE
        WHERE id = (
            SELECT id FROM products
            WHERE type=$1 AND is_sold=FALSE
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        )
        RETURNING *
    """, order["product_type"])

    if not product:
        await bot.send_message(order["user_id"], "❌ Out of stock")
        return {"error": "no stock"}

    # 🔥 deliver
    await bot.send_message(
        order["user_id"],
        f"✅ Delivered ({order['product_type']}):\n{product['value']}"
    )

    return {"ok": True}

# =========================
# REJECT
# =========================
@app.post("/reject/{order_id}")
async def reject(order_id: int):
    await execute(
        "UPDATE orders SET status='cancel' WHERE id=$1",
        order_id
    )
    return {"ok": True}

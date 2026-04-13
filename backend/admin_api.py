from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from db import fetch, fetchrow, execute
from aiogram import Bot
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# AUTH
security = HTTPBearer()
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "123456")

def verify(token=Depends(security)):
    if token.credentials != ADMIN_TOKEN:
        raise HTTPException(403)

# =========================
# ORDERS
# =========================
@app.get("/orders")
async def orders(user=Depends(verify)):
    return await fetch("SELECT * FROM orders ORDER BY created_at DESC")

# =========================
# PRODUCTS
# =========================
@app.get("/products")
async def products(user=Depends(verify)):
    return await fetch("SELECT * FROM products")

@app.post("/products")
async def add_product(type: str, value: str, user=Depends(verify)):
    await execute(
        "INSERT INTO products (type, value) VALUES ($1,$2)",
        type, value
    )
    return {"ok": True}

# =========================
# CONFIRM
# =========================
@app.post("/confirm/{order_id}")
async def confirm(order_id: int, user=Depends(verify)):
    order = await fetchrow("""
        UPDATE orders
        SET status='done', delivered=TRUE
        WHERE id=$1 AND delivered=FALSE
        RETURNING *
    """, order_id)

    if not order:
        return {"error": "done"}

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

    await bot.send_message(
        order["user_id"],
        f"✅ Delivered:\n{product['value']}"
    )

    return {"ok": True}

# =========================
# REJECT
# =========================
@app.post("/reject/{order_id}")
async def reject(order_id: int, user=Depends(verify)):
    await execute("UPDATE orders SET status='cancel' WHERE id=$1", order_id)
    return {"ok": True}

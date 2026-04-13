from db import (
    get_categories,
    get_products_by_category,
    get_product,
    purchase_product,
)


def fetch_categories():
    return get_categories()


def fetch_products_by_category(category_id: int):
    return get_products_by_category(category_id)


def fetch_product(product_id: int):
    row = get_product(product_id)
    if not row:
        return None

    product_id, category_id, title, price, stock, description = row
    return {
        "id": int(product_id),
        "category_id": int(category_id),
        "title": title,
        "price": float(price),
        "stock": int(stock or 0),
        "description": description or "",
    }


def build_product_text(product: dict) -> str:
    return (
        f"🛍 <b>Product Details</b>\n\n"
        f"📌 Name: <b>{product['title']}</b>\n"
        f"💰 Price: <b>{product['price']:.2f} USDT</b>\n"
        f"📦 Stock: <b>{product['stock']}</b>\n\n"
        f"📝 Note:\n"
        f"{product['description'] or 'Please test with a small quantity first.'}"
    )


def validate_quantity_text(text: str):
    raw = (text or "").strip()

    if not raw.isdigit():
        return None, "❌ Please enter a valid number"

    qty = int(raw)

    if qty <= 0:
        return None, "❌ Quantity must be greater than 0"

    if qty > 100000:
        return None, "❌ Quantity too large"

    return qty, None


def create_product_order(user_id: int, product_id: int, qty: int):
    return purchase_product(user_id, product_id, qty)


def build_order_success_text(order: dict) -> str:
    return (
        f"✅ <b>Order created successfully</b>\n\n"
        f"🆔 Order ID: <code>{order['order_id']}</code>\n"
        f"📦 Product: <b>{order['title']}</b>\n"
        f"🔢 Quantity: <b>{order['qty']}</b>\n"
        f"💵 Amount: <b>{order['amount']:.2f} USDT</b>\n"
        f"📌 Status: <b>{order['status']}</b>"
    )

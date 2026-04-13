from aiogram import Router, types, F

from db import get_user_orders

router = Router()


def format_order_status(status: str) -> str:
    mapping = {
        "pending": "⏳ Pending",
        "paid": "✅ Paid",
        "done": "✅ Done",
        "cancelled": "❌ Cancelled",
        "rejected": "❌ Rejected",
    }
    return mapping.get(status, status)


def build_orders_text(user_id: int) -> str:
    rows = get_user_orders(user_id)

    if not rows:
        return "📦 No purchase history yet"

    lines = ["📦 <b>Purchase History</b>", ""]

    for order_id, title, qty, amount, status, created_at in rows[:20]:
        lines.append(
            f"• <b>#{order_id}</b> | {title or '-'}\n"
            f"  Qty: {qty} | {amount:.2f} USDT | {format_order_status(status)}"
        )

    return "\n".join(lines)


@router.callback_query(F.data == "menu:orders")
async def menu_orders(c: types.CallbackQuery):
    await c.message.answer(
        build_orders_text(c.from_user.id),
        parse_mode="HTML"
    )
    await c.answer()

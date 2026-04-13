from datetime import datetime

from db import create_topup_order, get_user, get_user_topup_orders


def fmt_ts(ts: int) -> str:
    try:
        return datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "-"


def format_status(status: str) -> str:
    mapping = {
        "pending": "⏳ Pending",
        "paid": "✅ Paid",
        "rejected": "❌ Rejected",
        "cancelled": "🚫 Cancelled",
    }
    return mapping.get(status, status)


def get_user_balance(user_id: int) -> float:
    row = get_user(user_id)
    if not row:
        return 0.0
    return float(row[3] or 0)


def build_topup_menu_text(user_id: int) -> str:
    balance = get_user_balance(user_id)
    return (
        f"💳 <b>Wallet</b>\n\n"
        f"💰 Current Balance: <b>{balance:.2f} USDT</b>\n\n"
        f"Please choose a top-up amount:"
    )


def validate_custom_amount(text: str):
    raw = (text or "").strip()

    try:
        amount = float(raw)
    except Exception:
        return None, "❌ Invalid amount"

    if amount <= 0:
        return None, "❌ Amount must be greater than 0"

    if amount < 1:
        return None, "❌ Minimum top-up is 1 USDT"

    if amount > 100000:
        return None, "❌ Maximum top-up is 100000 USDT"

    return amount, None


def create_user_topup_order(user_id: int, amount: float) -> int:
    return create_topup_order(user_id, amount)


def build_topup_created_text(order_id: int, amount: float, payment_address: str) -> str:
    return (
        f"✅ <b>Top-up order created</b>\n\n"
        f"🆔 Order ID: <code>{order_id}</code>\n"
        f"💵 Amount: <b>{amount:.2f} USDT</b>\n"
        f"🏦 Address: <code>{payment_address}</code>\n\n"
        f"⚠️ Please send the exact amount and keep your transaction ID."
    )


def build_topup_orders_text(user_id: int) -> str:
    rows = get_user_topup_orders(user_id)

    if not rows:
        return "📜 No top-up history yet"

    lines = ["📜 <b>Top-up History</b>", ""]

    for order_id, amount, status, created_at in rows[:20]:
        lines.append(
            f"• <b>#{order_id}</b> | {amount:.2f} USDT | {format_status(status)}\n"
            f"  🕒 {fmt_ts(created_at)}"
        )

    return "\n".join(lines)

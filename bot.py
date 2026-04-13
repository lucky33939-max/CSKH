import os
import asyncio

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db import (
    init_db,
    close_db,
    get_or_create_user_from_tg,
    get_user_lang,
    set_user_lang,
    get_promo_text,
    list_categories,
    get_category,
    list_featured_services,
    list_services_by_category,
    get_service,
    create_order,
    user_orders,
    user_orders_count,
    get_user_invoices,
    get_invoice_by_order_id,
    all_user_ids,
    seed_sample_data,
    add_category,
    add_service,
    set_featured,
    set_balance,
    set_promo_text,
    list_services_admin,
)

load_dotenv()


BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@ZZB339")
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/ZXZ368")
SHOP_NAME = os.getenv("SHOP_NAME", "♛『 至尊机甲 』")
START_BANNER_URL = os.getenv("START_BANNER_URL", "").strip()
PAYMENT_TEXT = os.getenv(
    "PAYMENT_TEXT",
    "USDT TRC20\nWallet: YOUR_WALLET_ADDRESS\nAfter payment, please send receipt to support."
)

if not BOT_TOKEN:
    raise ValueError("Missing BOT_TOKEN")

SUPPORT_LINK = f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# =========================
# TRANSLATIONS (EN + ZH)
# =========================

TRANSLATIONS = {
    "en": {
        "welcome": (
            f"🔥 Welcome to {SHOP_NAME}\n\n"
            "✅ Professional Telegram services\n"
            "✅ Fast handling and reliable support\n"
            "✅ Premium service packages for individuals and communities\n\n"
            "🎁 Today’s promotions are live\n"
            "👇 Please choose an option below to begin\n\n"
            f"🆘 Support: {SUPPORT_USERNAME}\n"
            f"📢 Channel: @ZXZ368"
        ),
        "choose_action": "Choose an option below:",
        "btn_hot": "🔥 Hot Services",
        "btn_catalog": "🛍 Catalog",
        "btn_promo": "💎 Promotions",
        "btn_topup": "💳 Top Up",
        "btn_balance": "💰 Balance",
        "btn_orders": "📦 Orders",
        "btn_invoice": "🧾 Invoices",
        "btn_language": "🌍 Language",
        "btn_support": "🆘 Support",
        "btn_channel": "📢 Channel",
        "btn_center": "👤 My Center",

        "language_title": "🌍 Please choose your language:",
        "language_updated_en": "✅ Language changed to English.",
        "language_updated_zh": "✅ 语言已切换为中文。",

        "back": "⬅️ Back",
        "back_menu": "🏠 Main Menu",
        "buy_now": "🛒 Buy Now",
        "contact_support": "🆘 Contact Support",
        "open_channel": "📢 Open Channel",
        "topup_now": "💳 Top Up Now",
        "view_invoice": "🧾 View Invoice",

        "hot_title": "🔥 Featured services\n\nChoose a package below:",
        "catalog_title": "🛍 Service categories\n\nPlease choose a category:",
        "services_title": "📂 {category}\n\nChoose a service to view:",
        "service_detail": (
            "✨ {title}\n"
            "🏷 {badge}\n"
            "💵 Price: {price:.2f} USDT\n\n"
            "{description}\n\n"
            "📌 After payment, admin will process your order and contact you."
        ),

        "promo_title": "💎 Today's promotions\n\n{promo}",
        "default_promo": (
            "🎁 Top up 100 USDT: get 5% bonus\n"
            "🎁 Top up 300 USDT: get 10% bonus\n"
            "🎁 Selected service packages are on limited discount"
        ),

        "balance_text": "💰 Current balance: {balance:.2f} USDT",
        "balance_not_enough": "Insufficient balance. Please top up to continue.",
        "buy_success": (
            "✅ Order created successfully\n\n"
            "📦 Service: {title}\n"
            "💵 Price: {price:.2f} USDT\n"
            "🧾 Order ID: #{order_id}\n\n"
            "Admin will process your request soon."
        ),

        "orders_empty": "You have no orders yet.",
        "orders_title": "📦 Your latest 10 orders:\n\n",
        "orders_line": "#{id} - {title} - {price:.2f} USDT - {status} - {created_at}\n",

        "invoices_empty": "You do not have any invoices yet.",
        "invoices_title": "🧾 Your recent invoices:\n\nChoose one invoice to view details.",
        "invoice_paid": "Paid",
        "invoice_detail": (
            "🧾 INVOICE\n\n"
            "Invoice No: {invoice_no}\n"
            "Order ID: #{order_id}\n"
            "Customer: {name}\n"
            "User ID: {user_id}\n"
            "Service: {service}\n"
            "Amount: {amount:.2f} USDT\n"
            "Status: {status}\n"
            "Created At: {created_at}\n\n"
            "Support: {support}"
        ),

        "center_text": (
            "🌞 Hello, {name}\n\n"
            "🆔 User ID: {user_id}\n"
            "📅 Registered: {created_at}\n"
            "💰 Balance: {balance:.2f} USDT\n"
            "💸 Total spent: {spent:.2f} USDT\n"
            "📦 Total orders: {orders}\n\n"
            "Please choose an option below."
        ),

        "support_text": (
            "🆘 Customer Support\n\n"
            f"• Support: {SUPPORT_USERNAME}\n"
            f"• Channel: {CHANNEL_URL}\n\n"
            "If you need service consultation or payment confirmation, please contact support."
        ),

        "channel_text": "📢 Official channel of the shop:",
        "topup_title": "💳 Top Up\n\nChoose an amount below or contact support after payment.",
        "topup_info": (
            "💳 Top up {amount} USDT\n\n"
            "{payment_text}\n\n"
            f"🆘 Support: {SUPPORT_USERNAME}\n"
            "📌 Send your Telegram ID: {user_id}"
        ),

        "no_categories": "No categories yet.",
        "no_services": "No services in this category yet.",
        "service_not_found": "Service not found.",

        "admin_only": "You are not allowed to use this command.",
        "admin_help": (
            "⚙️ Admin commands\n\n"
            "/seed\n"
            "/addcategory name_en | name_zh\n"
            "/addservice category_id | title | price | badge | desc_en | desc_zh\n"
            "/feature service_id | 1 or 0\n"
            "/setbalance telegram_id | amount\n"
            "/promo promotion text\n"
            "/broadcast message\n"
            "/services"
        ),
        "seed_done": "✅ Sample data created.",
        "category_added": "✅ Category added.",
        "service_added": "✅ Service added.",
        "feature_updated": "✅ Featured updated.",
        "balance_updated": "✅ Balance updated.",
        "promo_updated": "✅ Promotion updated.",
        "broadcast_done": "✅ Broadcast sent.\nSuccess: {ok}\nFailed: {fail}",
        "services_empty": "No services yet.",
        "services_admin_title": "📋 Service list:\n\n",
        "services_admin_line": "ID {id} | {title} | {price:.2f} USDT | Cat {category_id} | Featured: {featured}\n",

        "bad_addcategory": "Wrong syntax.\nExample:\n/addcategory Bot Rental | 机器人租用",
        "bad_addservice": "Wrong syntax.\nExample:\n/addservice 1 | Monthly Bot Rental | 49 | HOT | English description | 中文描述",
        "bad_feature": "Wrong syntax.\nExample:\n/feature 1 | 1",
        "bad_setbalance": "Wrong syntax.\nExample:\n/setbalance 123456789 | 100",
        "broadcast_empty": "Broadcast content is empty."
    },

    "zh": {
        "welcome": (
            f"🔥 欢迎来到 {SHOP_NAME}\n\n"
            "✅ 专业 Telegram 服务\n"
            "✅ 处理高效，支持可靠\n"
            "✅ 为个人与社群提供优质服务套餐\n\n"
            "🎁 今日优惠已开启\n"
            "👇 请选择下方功能开始\n\n"
            f"🆘 客服: {SUPPORT_USERNAME}\n"
            f"📢 频道: @ZXZ368"
        ),
        "choose_action": "请选择下面的功能：",
        "btn_hot": "🔥 热门服务",
        "btn_catalog": "🛍 服务目录",
        "btn_promo": "💎 优惠活动",
        "btn_topup": "💳 充值",
        "btn_balance": "💰 余额",
        "btn_orders": "📦 订单",
        "btn_invoice": "🧾 发票",
        "btn_language": "🌍 语言",
        "btn_support": "🆘 客服",
        "btn_channel": "📢 频道",
        "btn_center": "👤 个人中心",

        "language_title": "🌍 请选择语言：",
        "language_updated_en": "✅ Language changed to English.",
        "language_updated_zh": "✅ 语言已切换为中文。",

        "back": "⬅️ 返回",
        "back_menu": "🏠 主菜单",
        "buy_now": "🛒 立即购买",
        "contact_support": "🆘 联系客服",
        "open_channel": "📢 打开频道",
        "topup_now": "💳 立即充值",
        "view_invoice": "🧾 查看发票",

        "hot_title": "🔥 热门服务\n\n请选择下面的套餐：",
        "catalog_title": "🛍 服务分类\n\n请选择一个分类：",
        "services_title": "📂 {category}\n\n请选择要查看的服务：",
        "service_detail": (
            "✨ {title}\n"
            "🏷 {badge}\n"
            "💵 价格: {price:.2f} USDT\n\n"
            "{description}\n\n"
            "📌 付款后，管理员将处理您的订单并联系您。"
        ),

        "promo_title": "💎 今日优惠\n\n{promo}",
        "default_promo": (
            "🎁 充值 100 USDT：赠送 5%\n"
            "🎁 充值 300 USDT：赠送 10%\n"
            "🎁 部分服务套餐限时优惠中"
        ),

        "balance_text": "💰 当前余额: {balance:.2f} USDT",
        "balance_not_enough": "余额不足，请先充值。",
        "buy_success": (
            "✅ 订单创建成功\n\n"
            "📦 服务: {title}\n"
            "💵 价格: {price:.2f} USDT\n"
            "🧾 订单号: #{order_id}\n\n"
            "管理员会尽快处理您的需求。"
        ),

        "orders_empty": "您还没有订单。",
        "orders_title": "📦 最近 10 个订单：\n\n",
        "orders_line": "#{id} - {title} - {price:.2f} USDT - {status} - {created_at}\n",

        "invoices_empty": "您还没有任何发票。",
        "invoices_title": "🧾 您最近的发票：\n\n请选择一个发票查看详情。",
        "invoice_paid": "已支付",
        "invoice_detail": (
            "🧾 发票\n\n"
            "发票号: {invoice_no}\n"
            "订单号: #{order_id}\n"
            "客户: {name}\n"
            "用户ID: {user_id}\n"
            "服务: {service}\n"
            "金额: {amount:.2f} USDT\n"
            "状态: {status}\n"
            "时间: {created_at}\n\n"
            "客服: {support}"
        ),

        "center_text": (
            "🌞 您好，{name}\n\n"
            "🆔 用户ID: {user_id}\n"
            "📅 注册时间: {created_at}\n"
            "💰 余额: {balance:.2f} USDT\n"
            "💸 总消费: {spent:.2f} USDT\n"
            "📦 总订单: {orders}\n\n"
            "请选择下面的功能。"
        ),

        "support_text": (
            "🆘 客户支持\n\n"
            f"• 客服: {SUPPORT_USERNAME}\n"
            f"• 频道: {CHANNEL_URL}\n\n"
            "如果您需要服务咨询或付款确认，请联系客服。"
        ),

        "channel_text": "📢 商店官方频道：",
        "topup_title": "💳 充值\n\n请选择金额，付款后请联系客户支持。",
        "topup_info": (
            "💳 充值 {amount} USDT\n\n"
            "{payment_text}\n\n"
            f"🆘 客服: {SUPPORT_USERNAME}\n"
            "📌 发送您的 Telegram ID: {user_id}"
        ),

        "no_categories": "暂无分类。",
        "no_services": "该分类下暂无服务。",
        "service_not_found": "未找到服务。",

        "admin_only": "您没有权限使用此命令。",
        "admin_help": (
            "⚙️ 管理员命令\n\n"
            "/seed\n"
            "/addcategory name_en | name_zh\n"
            "/addservice category_id | title | price | badge | desc_en | desc_zh\n"
            "/feature service_id | 1 或 0\n"
            "/setbalance telegram_id | amount\n"
            "/promo 优惠内容\n"
            "/broadcast 内容\n"
            "/services"
        ),
        "seed_done": "✅ 示例数据已创建。",
        "category_added": "✅ 已添加分类。",
        "service_added": "✅ 已添加服务。",
        "feature_updated": "✅ 已更新热门状态。",
        "balance_updated": "✅ 余额已更新。",
        "promo_updated": "✅ 优惠内容已更新。",
        "broadcast_done": "✅ 群发完成。\n成功: {ok}\n失败: {fail}",
        "services_empty": "暂无服务。",
        "services_admin_title": "📋 服务列表：\n\n",
        "services_admin_line": "ID {id} | {title} | {price:.2f} USDT | 分类 {category_id} | 热门: {featured}\n",

        "bad_addcategory": "格式错误。\n例如：\n/addcategory Bot Rental | 机器人租用",
        "bad_addservice": "格式错误。\n例如：\n/addservice 1 | Monthly Bot Rental | 49 | HOT | English description | 中文描述",
        "bad_feature": "格式错误。\n例如：\n/feature 1 | 1",
        "bad_setbalance": "格式错误。\n例如：\n/setbalance 123456789 | 100",
        "broadcast_empty": "群发内容为空。"
    }
}


def t(lang: str, key: str, **kwargs):
    lang = lang if lang in TRANSLATIONS else "zh"
    text = TRANSLATIONS[lang].get(key, TRANSLATIONS["zh"].get(key, key))
    return text.format(**kwargs) if kwargs else text


def match_key(text: str, key: str):
    if not text:
        return False
    return text in [TRANSLATIONS[lang][key] for lang in TRANSLATIONS]


def make_invoice_no(order_id: int, created_at):
    return f"INV-{created_at:%Y%m%d}-{order_id:06d}"


# =========================
# KEYBOARDS
# =========================

def main_menu(lang: str):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(lang, "btn_hot")), KeyboardButton(text=t(lang, "btn_catalog"))],
            [KeyboardButton(text=t(lang, "btn_promo")), KeyboardButton(text=t(lang, "btn_topup"))],
            [KeyboardButton(text=t(lang, "btn_balance")), KeyboardButton(text=t(lang, "btn_orders"))],
            [KeyboardButton(text=t(lang, "btn_invoice")), KeyboardButton(text=t(lang, "btn_language"))],
            [KeyboardButton(text=t(lang, "btn_support")), KeyboardButton(text=t(lang, "btn_channel"))],
            [KeyboardButton(text=t(lang, "btn_center"))],
        ],
        resize_keyboard=True
    )


def language_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇺🇸 English", callback_data="lang:en")],
            [InlineKeyboardButton(text="🇨🇳 中文", callback_data="lang:zh")],
        ]
    )


def support_kb(lang: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "contact_support"), url=SUPPORT_LINK)],
            [InlineKeyboardButton(text=t(lang, "open_channel"), url=CHANNEL_URL)],
            [InlineKeyboardButton(text=t(lang, "back_menu"), callback_data="menu")],
        ]
    )


def topup_kb(lang: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="10 USDT", callback_data="topup:10"),
                InlineKeyboardButton(text="50 USDT", callback_data="topup:50"),
            ],
            [
                InlineKeyboardButton(text="100 USDT", callback_data="topup:100"),
                InlineKeyboardButton(text="200 USDT", callback_data="topup:200"),
            ],
            [
                InlineKeyboardButton(text="500 USDT", callback_data="topup:500"),
                InlineKeyboardButton(text="1000 USDT", callback_data="topup:1000"),
            ],
            [InlineKeyboardButton(text=t(lang, "contact_support"), url=SUPPORT_LINK)],
            [InlineKeyboardButton(text=t(lang, "back_menu"), callback_data="menu")],
        ]
    )


def back_to_menu_inline(lang: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "back_menu"), callback_data="menu")]
        ]
    )

# =========================
# UI HELPERS
# =========================

def category_name(row, lang):
    return row["name_en"] if lang == "en" else row["name_zh"]


def service_desc(row, lang):
    return row["desc_en"] if lang == "en" else row["desc_zh"]


async def send_home(target, lang: str):
    text = t(lang, "welcome")
    if isinstance(target, Message):
        if START_BANNER_URL:
            await target.answer_photo(
                photo=START_BANNER_URL,
                caption=text,
                reply_markup=main_menu(lang)
            )
        else:
            await target.answer(text, reply_markup=main_menu(lang))
    else:
        await target.message.answer(text, reply_markup=main_menu(lang))


async def send_categories(target, lang: str):
    rows = await list_categories()
    if not rows:
        if isinstance(target, Message):
            await target.answer(t(lang, "no_categories"))
        else:
            await target.message.edit_text(t(lang, "no_categories"))
        return

    kb = InlineKeyboardBuilder()
    for row in rows:
        kb.button(text=category_name(row, lang), callback_data=f"cat:{row['id']}")
    kb.button(text=t(lang, "back_menu"), callback_data="menu")
    kb.adjust(1)

    if isinstance(target, Message):
        await target.answer(t(lang, "catalog_title"), reply_markup=kb.as_markup())
    else:
        await target.message.edit_text(t(lang, "catalog_title"), reply_markup=kb.as_markup())


async def send_featured(target, lang: str):
    rows = await list_featured_services()
    if not rows:
        if isinstance(target, Message):
            await target.answer(t(lang, "services_empty"))
        else:
            await target.message.edit_text(t(lang, "services_empty"))
        return

    kb = InlineKeyboardBuilder()
    for row in rows:
        kb.button(
            text=f"{row['title']} - {float(row['price']):.2f} USDT",
            callback_data=f"service:{row['id']}"
        )
    kb.button(text=t(lang, "back_menu"), callback_data="menu")
    kb.adjust(1)

    if isinstance(target, Message):
        await target.answer(t(lang, "hot_title"), reply_markup=kb.as_markup())
    else:
        await target.message.edit_text(t(lang, "hot_title"), reply_markup=kb.as_markup())


async def send_services_by_category(call: CallbackQuery, lang: str, category_id: int):
    category = await get_category(category_id)
    if not category:
        await call.answer(t(lang, "no_categories"), show_alert=True)
        return

    rows = await list_services_by_category(category_id)
    if not rows:
        await call.message.edit_text(
            t(lang, "no_services"),
            reply_markup=back_to_menu_inline(lang)
        )
        return

    kb = InlineKeyboardBuilder()
    for row in rows:
        kb.button(
            text=f"{row['title']} - {float(row['price']):.2f} USDT",
            callback_data=f"service:{row['id']}"
        )
    kb.button(text=t(lang, "back"), callback_data="catalog")
    kb.button(text=t(lang, "back_menu"), callback_data="menu")
    kb.adjust(1)

    await call.message.edit_text(
        t(lang, "services_title", category=category_name(category, lang)),
        reply_markup=kb.as_markup()
    )


async def send_service_detail(call: CallbackQuery, lang: str, service_id: int):
    row = await get_service(service_id)
    if not row:
        await call.answer(t(lang, "service_not_found"), show_alert=True)
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "buy_now"), callback_data=f"buy:{service_id}")],
            [InlineKeyboardButton(text=t(lang, "contact_support"), url=SUPPORT_LINK)],
            [InlineKeyboardButton(text=t(lang, "back"), callback_data=f"cat:{row['category_id']}")],
            [InlineKeyboardButton(text=t(lang, "back_menu"), callback_data="menu")],
        ]
    )

    await call.message.edit_text(
        t(
            lang,
            "service_detail",
            title=row["title"],
            badge=row["badge"],
            price=float(row["price"]),
            description=service_desc(row, lang)
        ),
        reply_markup=kb
    )


async def send_invoices_list(target, lang: str, tg_id: int):
    rows = await get_user_invoices(tg_id)
    if not rows:
        if isinstance(target, Message):
            await target.answer(t(lang, "invoices_empty"))
        else:
            await target.message.edit_text(t(lang, "invoices_empty"))
        return

    kb = InlineKeyboardBuilder()
    for row in rows:
        invoice_no = make_invoice_no(row["id"], row["created_at"])
        kb.button(
            text=f"{invoice_no} - {float(row['price']):.2f} USDT",
            callback_data=f"invoice:{row['id']}"
        )
    kb.button(text=t(lang, "back_menu"), callback_data="menu")
    kb.adjust(1)

    if isinstance(target, Message):
        await target.answer(t(lang, "invoices_title"), reply_markup=kb.as_markup())
    else:
        await target.message.edit_text(t(lang, "invoices_title"), reply_markup=kb.as_markup())


async def send_invoice_detail(call: CallbackQuery, lang: str, order_id: int):
    row = await get_invoice_by_order_id(order_id, call.from_user.id)
    if not row:
        await call.answer(t(lang, "service_not_found"), show_alert=True)
        return

    invoice_no = make_invoice_no(row["id"], row["created_at"])
    status_text = t(lang, "invoice_paid") if row["status"] == "paid" else row["status"]

    text = t(
        lang,
        "invoice_detail",
        invoice_no=invoice_no,
        order_id=row["id"],
        name=call.from_user.full_name,
        user_id=call.from_user.id,
        service=row["title"],
        amount=float(row["price"]),
        status=status_text,
        created_at=row["created_at"].strftime("%Y-%m-%d %H:%M"),
        support=SUPPORT_USERNAME
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "back"), callback_data="invoice_list")],
            [InlineKeyboardButton(text=t(lang, "contact_support"), url=SUPPORT_LINK)],
            [InlineKeyboardButton(text=t(lang, "back_menu"), callback_data="menu")],
        ]
    )

    await call.message.edit_text(text, reply_markup=kb)


# =========================
# USER HANDLERS
# =========================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user = await get_or_create_user_from_tg(message.from_user)
    await send_home(message, user["language"] or "zh")


@dp.message(lambda m: m.text and match_key(m.text, "btn_language"))
async def menu_language(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)
    await message.answer(t(lang, "language_title"), reply_markup=language_kb())


@dp.callback_query(F.data.startswith("lang:"))
async def cb_language(call: CallbackQuery):
    await get_or_create_user_from_tg(call.from_user)
    lang = call.data.split(":")[1]
    if lang not in TRANSLATIONS:
        lang = "zh"

    await set_user_lang(call.from_user.id, lang)
    await call.message.edit_text(t(lang, f"language_updated_{lang}"))
    await call.message.answer(t(lang, "choose_action"), reply_markup=main_menu(lang))
    await call.answer()


@dp.message(lambda m: m.text and match_key(m.text, "btn_hot"))
async def menu_hot(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)
    await send_featured(message, lang)


@dp.message(lambda m: m.text and match_key(m.text, "btn_catalog"))
async def menu_catalog(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)
    await send_categories(message, lang)


@dp.message(lambda m: m.text and match_key(m.text, "btn_promo"))
async def menu_promo(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)
    promo = await get_promo_text(lang)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "topup_now"), callback_data="open_topup")],
            [InlineKeyboardButton(text=t(lang, "back_menu"), callback_data="menu")]
        ]
    )

    await message.answer(t(lang, "promo_title", promo=promo), reply_markup=kb)


@dp.message(lambda m: m.text and match_key(m.text, "btn_topup"))
async def menu_topup(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)
    await message.answer(t(lang, "topup_title"), reply_markup=topup_kb(lang))


@dp.message(lambda m: m.text and match_key(m.text, "btn_balance"))
async def menu_balance(message: Message):
    user = await get_or_create_user_from_tg(message.from_user)
    lang = user["language"] or "zh"
    await message.answer(t(lang, "balance_text", balance=float(user["balance"])))


@dp.message(lambda m: m.text and match_key(m.text, "btn_orders"))
async def menu_orders(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)
    rows = await user_orders(message.from_user.id)

    if not rows:
        return await message.answer(t(lang, "orders_empty"))

    text = t(lang, "orders_title")
    for row in rows:
        text += t(
            lang,
            "orders_line",
            id=row["id"],
            title=row["title"],
            price=float(row["price"]),
            status=row["status"],
            created_at=row["created_at"].strftime("%Y-%m-%d %H:%M")
        )

    await message.answer(text)


@dp.message(lambda m: m.text and match_key(m.text, "btn_invoice"))
async def menu_invoices(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)
    await send_invoices_list(message, lang, message.from_user.id)


@dp.message(lambda m: m.text and match_key(m.text, "btn_support"))
async def menu_support(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)
    await message.answer(t(lang, "support_text"), reply_markup=support_kb(lang))


@dp.message(lambda m: m.text and match_key(m.text, "btn_channel"))
async def menu_channel(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "open_channel"), url=CHANNEL_URL)],
            [InlineKeyboardButton(text=t(lang, "back_menu"), callback_data="menu")]
        ]
    )
    await message.answer(t(lang, "channel_text"), reply_markup=kb)


@dp.message(lambda m: m.text and match_key(m.text, "btn_center"))
async def menu_center(message: Message):
    user = await get_or_create_user_from_tg(message.from_user)
    lang = user["language"] or "zh"
    total_orders = await user_orders_count(message.from_user.id)

    await message.answer(
        t(
            lang,
            "center_text",
            name=message.from_user.full_name,
            user_id=message.from_user.id,
            created_at=user["created_at"].strftime("%Y-%m-%d %H:%M"),
            balance=float(user["balance"]),
            spent=float(user["total_spent"]),
            orders=total_orders
        ),
        reply_markup=main_menu(lang)
    )


# =========================
# CALLBACK HANDLERS
# =========================

@dp.callback_query(F.data == "menu")
async def cb_menu(call: CallbackQuery):
    lang = await get_user_lang(call.from_user.id)
    await call.message.answer(t(lang, "choose_action"), reply_markup=main_menu(lang))
    await call.answer()


@dp.callback_query(F.data == "catalog")
async def cb_catalog(call: CallbackQuery):
    lang = await get_user_lang(call.from_user.id)
    await send_categories(call, lang)
    await call.answer()


@dp.callback_query(F.data == "open_topup")
async def cb_open_topup(call: CallbackQuery):
    lang = await get_user_lang(call.from_user.id)
    await call.message.answer(t(lang, "topup_title"), reply_markup=topup_kb(lang))
    await call.answer()


@dp.callback_query(F.data.startswith("cat:"))
async def cb_category(call: CallbackQuery):
    lang = await get_user_lang(call.from_user.id)
    category_id = int(call.data.split(":")[1])
    await send_services_by_category(call, lang, category_id)
    await call.answer()


@dp.callback_query(F.data.startswith("service:"))
async def cb_service(call: CallbackQuery):
    lang = await get_user_lang(call.from_user.id)
    service_id = int(call.data.split(":")[1])
    await send_service_detail(call, lang, service_id)
    await call.answer()


@dp.callback_query(F.data.startswith("buy:"))
async def cb_buy(call: CallbackQuery):
    await get_or_create_user_from_tg(call.from_user)
    lang = await get_user_lang(call.from_user.id)
    service_id = int(call.data.split(":")[1])

    ok, result = await create_order(call.from_user.id, service_id)
    if not ok:
        if result == "balance_not_enough":
            await call.answer(t(lang, "balance_not_enough"), show_alert=True)
            await call.message.answer(t(lang, "topup_title"), reply_markup=topup_kb(lang))
            return

        await call.answer(t(lang, result), show_alert=True)
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "view_invoice"), callback_data=f"invoice:{result['order_id']}")],
            [InlineKeyboardButton(text=t(lang, "contact_support"), url=SUPPORT_LINK)],
            [InlineKeyboardButton(text=t(lang, "back_menu"), callback_data="menu")]
        ]
    )

    await call.message.answer(
        t(
            lang,
            "buy_success",
            title=result["title"],
            price=result["price"],
            order_id=result["order_id"]
        ),
        reply_markup=kb
    )

    if ADMIN_ID:
        try:
            await bot.send_message(
                ADMIN_ID,
                f"🆕 New order\n"
                f"User: {call.from_user.full_name} ({call.from_user.id})\n"
                f"Service: {result['title']}\n"
                f"Price: {result['price']:.2f} USDT\n"
                f"Order ID: #{result['order_id']}"
            )
        except Exception:
            pass

    await call.answer("OK")


@dp.callback_query(F.data.startswith("topup:"))
async def cb_topup(call: CallbackQuery):
    lang = await get_user_lang(call.from_user.id)
    amount = call.data.split(":")[1]
    await call.message.answer(
        t(
            lang,
            "topup_info",
            amount=amount,
            payment_text=PAYMENT_TEXT,
            user_id=call.from_user.id
        ),
        reply_markup=support_kb(lang)
    )
    await call.answer()


@dp.callback_query(F.data == "invoice_list")
async def cb_invoice_list(call: CallbackQuery):
    lang = await get_user_lang(call.from_user.id)
    await send_invoices_list(call, lang, call.from_user.id)
    await call.answer()


@dp.callback_query(F.data.startswith("invoice:"))
async def cb_invoice_detail(call: CallbackQuery):
    lang = await get_user_lang(call.from_user.id)
    order_id = int(call.data.split(":")[1])
    await send_invoice_detail(call, lang, order_id)
    await call.answer()


# =========================
# ADMIN COMMANDS
# =========================

def is_admin(user_id: int):
    return user_id == ADMIN_ID


@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)
    if not is_admin(message.from_user.id):
        return await message.answer(t(lang, "admin_only"))
    await message.answer(t(lang, "admin_help"))


@dp.message(Command("seed"))
async def cmd_seed(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)

    if not is_admin(message.from_user.id):
        return await message.answer(t(lang, "admin_only"))

    await seed_sample_data()
    await message.answer(t(lang, "seed_done"))

@dp.message(Command("addcategory"))
async def cmd_addcategory(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)

    if not is_admin(message.from_user.id):
        return await message.answer(t(lang, "admin_only"))

    try:
        raw = message.text.replace("/addcategory", "", 1).strip()
        name_en, name_zh = [x.strip() for x in raw.split("|", 1)]
        await add_category(name_en, name_zh)
        await message.answer(t(lang, "category_added"))
    except Exception:
        await message.answer(t(lang, "bad_addcategory"))

@dp.message(Command("addservice"))
async def cmd_addservice(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)

    if not is_admin(message.from_user.id):
        return await message.answer(t(lang, "admin_only"))

    try:
        raw = message.text.replace("/addservice", "", 1).strip()
        parts = [x.strip() for x in raw.split("|", 5)]

        category_id = int(parts[0])
        title = parts[1]
        price = float(parts[2])
        badge = parts[3]
        desc_en = parts[4]
        desc_zh = parts[5]

        await add_service(category_id, title, price, badge, desc_en, desc_zh)
        await message.answer(t(lang, "service_added"))
    except Exception:
        await message.answer(t(lang, "bad_addservice"))


@dp.message(Command("feature"))
async def cmd_feature(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)

    if not is_admin(message.from_user.id):
        return await message.answer(t(lang, "admin_only"))

    try:
        raw = message.text.replace("/feature", "", 1).strip()
        service_id, val = [x.strip() for x in raw.split("|", 1)]
        await set_featured(int(service_id), val == "1")
        await message.answer(t(lang, "feature_updated"))
    except Exception:
        await message.answer(t(lang, "bad_feature"))

@dp.message(Command("setbalance"))
async def cmd_setbalance(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)

    if not is_admin(message.from_user.id):
        return await message.answer(t(lang, "admin_only"))

    try:
        raw = message.text.replace("/setbalance", "", 1).strip()
        tg_id, amount = [x.strip() for x in raw.split("|", 1)]
        await set_balance(int(tg_id), float(amount))
        await message.answer(t(lang, "balance_updated"))
    except Exception:
        await message.answer(t(lang, "bad_setbalance"))

@dp.message(Command("promo"))
async def cmd_promo(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)

    if not is_admin(message.from_user.id):
        return await message.answer(t(lang, "admin_only"))

    promo_text = message.text.replace("/promo", "", 1).strip()
    if not promo_text:
        promo_text = t(lang, "default_promo")

    await set_promo_text(promo_text)
    await message.answer(t(lang, "promo_updated"))

@dp.message(Command("services"))
async def cmd_services(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)

    if not is_admin(message.from_user.id):
        return await message.answer(t(lang, "admin_only"))

    rows = await list_services_admin()
    if not rows:
        return await message.answer(t(lang, "services_empty"))

    text = t(lang, "services_admin_title")
    for row in rows:
        text += t(
            lang,
            "services_admin_line",
            id=row["id"],
            title=row["title"],
            price=float(row["price"]),
            category_id=row["category_id"],
            featured=row["featured"]
        )

    await message.answer(text)
    
@dp.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)

    if not is_admin(message.from_user.id):
        return await message.answer(t(lang, "admin_only"))

    content = message.text.replace("/broadcast", "", 1).strip()
    if not content:
        return await message.answer(t(lang, "broadcast_empty"))

    user_ids = await all_user_ids()
    ok = 0
    fail = 0

    for uid in user_ids:
        try:
            await bot.send_message(uid, content)
            ok += 1
            await asyncio.sleep(0.08)
        except Exception:
            fail += 1

    await message.answer(t(lang, "broadcast_done", ok=ok, fail=fail))

# =========================
# STARTUP
# =========================
async def main():
    await init_db()
    print("Bot is running...")
    try:
        await dp.start_polling(bot)
    finally:
        await close_db()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())

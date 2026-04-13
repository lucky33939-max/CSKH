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
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from db import (
    init_db,
    close_db,
    get_or_create_user_from_tg,
    get_user,
    get_user_lang,
    set_user_lang,
    get_promo_text,
    list_categories,
    get_category,
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
    list_inventory_by_category,
    get_inventory_item,
    create_topup_request,
    confirm_topup_request,
    create_purchase_request,
    confirm_purchase_request,
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
dp = Dispatcher(storage=MemoryStorage())


class AmountFSM(StatesGroup):
    waiting_custom_topup = State()
    waiting_custom_purchase = State()


TRANSLATIONS = {
    "en": {
        "welcome": (
            f"♛ Welcome to {SHOP_NAME}\n\n"
            "✨ Premium Telegram concierge services\n"
            "✨ Featured now: Private Numbers & VIP Bots\n"
            "✨ Also available: Stars, Premium, Gifts, Advertising and Custom Services\n\n"
            "👇 Please choose a premium category below\n\n"
            f"🆘 Support: {SUPPORT_USERNAME}\n"
            f"📢 Channel: @ZXZ368"
        ),
        "choose_action": "Choose an option below:",
        "btn_language": "🌍 Language",
        "btn_ads": "📢 Advertising",
        "btn_cart_menu": "🛒 Cart",
        "btn_topup": "💳 Top Up",
        "btn_catalog": "🛍 All Services",
        "btn_support": "🆘 Support",

        "btn_anon": "👑 Private Numbers",
        "btn_vip_bot": "🤖 VIP Bots",
        "btn_stars": "⭐ Stars",
        "btn_premium": "⭐ Premium",
        "btn_gifts": "🎁 Gifts",
        "btn_back": "⬅️ Back",

        "btn_channel": "📢 Channel",
        "btn_fast_broadcast": "⚡ Fast Broadcast",
        "btn_balance": "💰 Balance",
        "btn_orders": "📦 Orders",
        "btn_invoice": "🧾 Invoices",

        "language_title": "🌍 Please choose your language:",
        "language_updated_en": "✅ Language changed to English.",
        "language_updated_zh": "✅ 语言已切换为中文。",

        "menu_cart_title": "🛒 Cart Menu\n\nChoose a premium category:",
        "menu_services_title": "🛍 All Services\n\nChoose a function below:",

        "anon_title": "👑 Private Numbers Collection\n\nChoose a number below:",
        "vip_bot_title": "🤖 VIP Bot Suites\n\nChoose a service below:",
        "stars_title": "⭐ Stars Services\n\nChoose a service below:",
        "premium_title": "⭐ Premium Services\n\nChoose a service below:",
        "gifts_title": "🎁 Gift Services\n\nChoose a service below:",
        "ads_title": "📢 Advertising Services\n\nChoose a service below:",
        "broadcast_title": "⚡ Fast Broadcast Services\n\nChoose a service below:",

        "back_menu": "🏠 Main Menu",
        "buy_now": "🛒 Buy Now",
        "contact_support": "🆘 Contact Support",
        "open_channel": "📢 Open Channel",
        "view_invoice": "🧾 View Invoice",

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

        "support_text": (
            "🆘 Customer Support\n\n"
            f"• Support: {SUPPORT_USERNAME}\n"
            f"• Channel: {CHANNEL_URL}\n\n"
            "If you need service consultation or payment confirmation, please contact support."
        ),
        "channel_text": "📢 Official channel of the shop:",
        "topup_title": "💳 Top Up\n\nChoose an amount below.",
        "topup_info": (
            "💳 Top up {amount} USDT\n\n"
            "{payment_text}\n\n"
            f"🆘 Support: {SUPPORT_USERNAME}\n"
            "📌 Telegram ID: {user_id}"
        ),

        "center_text": (
            "🌞 Hello, {name}\n\n"
            "🆔 User ID: {user_id}\n"
            "📅 Registered: {created_at}\n"
            "💰 Balance: {balance:.2f} USDT\n"
            "💸 Total spent: {spent:.2f} USDT\n"
            "📦 Total orders: {orders}\n"
        ),

        "no_categories": "No categories yet.",
        "no_services": "No services available.",
        "no_stock": "No stock available.",
        "service_not_found": "Service not found.",
        "item_not_found": "Item not found.",
        "choose_amount": "Please choose an amount:",
        "custom_amount_prompt_topup": "Please enter your custom top up amount (USDT).",
        "custom_amount_prompt_purchase": "Please enter your custom payment amount (USDT).",
        "invalid_amount": "Invalid amount. Please enter a number greater than 0.",
        "stock_empty": "Out of stock.",
        "topup_created": (
            "🧾 TOP UP INVOICE\n\n"
            "Invoice ID: #{invoice_id}\n"
            "Amount: {amount:.2f} USDT\n\n"
            "{payment_text}\n\n"
            "After payment, admin will confirm for you."
        ),
        "purchase_created": (
            "🧾 PURCHASE INVOICE\n\n"
            "Invoice ID: #{invoice_id}\n"
            "Item: {item}\n"
            "Amount: {amount:.2f} USDT\n\n"
            "{payment_text}\n\n"
            "After payment, admin will confirm and deliver your item."
        ),
        "topup_confirmed": "✅ Your top up has been confirmed.\n+{amount:.2f} USDT added to your balance.",
        "purchase_confirmed": "✅ Your purchase has been confirmed.\nItem: {item}",
        "admin_topup_notice": (
            "💳 New top up request\n\n"
            "User: {name}\n"
            "UID: {user_id}\n"
            "Amount: {amount:.2f} USDT\n"
            "Invoice: #{invoice_id}"
        ),
        "admin_purchase_notice": (
            "🛒 New purchase request\n\n"
            "User: {name}\n"
            "UID: {user_id}\n"
            "Item: {item}\n"
            "Amount: {amount:.2f} USDT\n"
            "Invoice: #{invoice_id}"
        ),
        "btn_confirm_topup": "✅ Confirm Top Up",
        "btn_confirm_purchase": "✅ Confirm Delivery",

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
            f"♛ 欢迎来到 {SHOP_NAME}\n\n"
            "✨ 高端 Telegram 礼宾服务\n"
            "✨ 当前主推：私享号码 与 VIP 机器人\n"
            "✨ 同时提供 Stars、Premium、礼品、广告与定制服务\n\n"
            "👇 请选择下方高端分类\n\n"
            f"🆘 客服: {SUPPORT_USERNAME}\n"
            f"📢 频道: @ZXZ368"
        ),
        "choose_action": "请选择下面的功能：",
        "btn_language": "🌍 语言",
        "btn_ads": "📢 广告服务",
        "btn_cart_menu": "🛒 购物区",
        "btn_topup": "💳 充值",
        "btn_catalog": "🛍 全部服务",
        "btn_support": "🆘 客服",

        "btn_anon": "👑 私享号码",
        "btn_vip_bot": "🤖 VIP 机器人",
        "btn_stars": "⭐ Stars",
        "btn_premium": "⭐ Premium",
        "btn_gifts": "🎁 礼品服务",
        "btn_back": "⬅️ 返回",

        "btn_channel": "📢 频道",
        "btn_fast_broadcast": "⚡ 快速推送",
        "btn_balance": "💰 余额",
        "btn_orders": "📦 订单",
        "btn_invoice": "🧾 发票",

        "language_title": "🌍 请选择语言：",
        "language_updated_en": "✅ Language changed to English.",
        "language_updated_zh": "✅ 语言已切换为中文。",

        "menu_cart_title": "🛒 购物区\n\n请选择高端分类：",
        "menu_services_title": "🛍 全部服务\n\n请选择下方功能：",

        "anon_title": "👑 私享号码系列\n\n请选择一个号码：",
        "vip_bot_title": "🤖 VIP 机器人套件\n\n请选择一个服务：",
        "stars_title": "⭐ Stars 服务\n\n请选择一个服务：",
        "premium_title": "⭐ Premium 服务\n\n请选择一个服务：",
        "gifts_title": "🎁 礼品服务\n\n请选择一个服务：",
        "ads_title": "📢 广告服务\n\n请选择一个服务：",
        "broadcast_title": "⚡ 快速推送服务\n\n请选择一个服务：",

        "back_menu": "🏠 主菜单",
        "buy_now": "🛒 立即购买",
        "contact_support": "🆘 联系客服",
        "open_channel": "📢 打开频道",
        "view_invoice": "🧾 查看发票",

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

        "support_text": (
            "🆘 客户支持\n\n"
            f"• 客服: {SUPPORT_USERNAME}\n"
            f"• 频道: {CHANNEL_URL}\n\n"
            "如果您需要服务咨询或付款确认，请联系客服。"
        ),
        "channel_text": "📢 商店官方频道：",
        "topup_title": "💳 充值\n\n请选择充值金额。",
        "topup_info": (
            "💳 充值 {amount} USDT\n\n"
            "{payment_text}\n\n"
            f"🆘 客服: {SUPPORT_USERNAME}\n"
            "📌 Telegram ID: {user_id}"
        ),

        "center_text": (
            "🌞 您好，{name}\n\n"
            "🆔 用户ID: {user_id}\n"
            "📅 注册时间: {created_at}\n"
            "💰 余额: {balance:.2f} USDT\n"
            "💸 总消费: {spent:.2f} USDT\n"
            "📦 总订单: {orders}\n"
        ),

        "no_categories": "暂无分类。",
        "no_services": "暂无服务。",
        "no_stock": "暂无库存。",
        "service_not_found": "未找到服务。",
        "item_not_found": "未找到商品。",
        "choose_amount": "请选择金额：",
        "custom_amount_prompt_topup": "请输入自定义充值金额（USDT）。",
        "custom_amount_prompt_purchase": "请输入自定义支付金额（USDT）。",
        "invalid_amount": "金额无效，请输入大于 0 的数字。",
        "stock_empty": "库存不足。",
        "topup_created": (
            "🧾 充值发票\n\n"
            "发票编号: #{invoice_id}\n"
            "金额: {amount:.2f} USDT\n\n"
            "{payment_text}\n\n"
            "付款后管理员将为您确认。"
        ),
        "purchase_created": (
            "🧾 购买发票\n\n"
            "发票编号: #{invoice_id}\n"
            "商品: {item}\n"
            "金额: {amount:.2f} USDT\n\n"
            "{payment_text}\n\n"
            "付款后管理员将确认并发货。"
        ),
        "topup_confirmed": "✅ 您的充值已确认。\n已为您到账 +{amount:.2f} USDT。",
        "purchase_confirmed": "✅ 您的订单已确认。\n商品: {item}",
        "admin_topup_notice": (
            "💳 新充值请求\n\n"
            "用户: {name}\n"
            "UID: {user_id}\n"
            "金额: {amount:.2f} USDT\n"
            "发票: #{invoice_id}"
        ),
        "admin_purchase_notice": (
            "🛒 新购买请求\n\n"
            "用户: {name}\n"
            "UID: {user_id}\n"
            "商品: {item}\n"
            "金额: {amount:.2f} USDT\n"
            "发票: #{invoice_id}"
        ),
        "btn_confirm_topup": "✅ 确认充值",
        "btn_confirm_purchase": "✅ 确认发货",

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
        "promo_updated": "✅ 已更新优惠内容。",
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
    return text in [TRANSLATIONS[lang][key] for lang in TRANSLATIONS if key in TRANSLATIONS[lang]]


def make_invoice_no(order_id: int, created_at):
    return f"INV-{created_at:%Y%m%d}-{order_id:06d}"


def main_menu(lang: str):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(lang, "btn_language")), KeyboardButton(text=t(lang, "btn_ads"))],
            [KeyboardButton(text=t(lang, "btn_cart_menu")), KeyboardButton(text=t(lang, "btn_topup"))],
            [KeyboardButton(text=t(lang, "btn_catalog")), KeyboardButton(text=t(lang, "btn_support"))],
        ],
        resize_keyboard=True
    )


def cart_menu(lang: str):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(lang, "btn_anon")), KeyboardButton(text=t(lang, "btn_vip_bot"))],
            [KeyboardButton(text=t(lang, "btn_stars")), KeyboardButton(text=t(lang, "btn_premium"))],
            [KeyboardButton(text=t(lang, "btn_gifts")), KeyboardButton(text=t(lang, "btn_topup"))],
            [KeyboardButton(text=t(lang, "btn_back"))],
        ],
        resize_keyboard=True
    )


def services_menu(lang: str):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(lang, "btn_channel")), KeyboardButton(text=t(lang, "btn_fast_broadcast"))],
            [KeyboardButton(text=t(lang, "btn_ads")), KeyboardButton(text=t(lang, "btn_balance"))],
            [KeyboardButton(text=t(lang, "btn_orders")), KeyboardButton(text=t(lang, "btn_invoice"))],
            [KeyboardButton(text=t(lang, "btn_support"))],
            [KeyboardButton(text=t(lang, "btn_back"))],
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
                InlineKeyboardButton(text="50", callback_data="topup:50"),
                InlineKeyboardButton(text="100", callback_data="topup:100"),
                InlineKeyboardButton(text="200", callback_data="topup:200"),
            ],
            [
                InlineKeyboardButton(text="500", callback_data="topup:500"),
                InlineKeyboardButton(text="1000", callback_data="topup:1000"),
                InlineKeyboardButton(text="2000", callback_data="topup:2000"),
            ],
            [
                InlineKeyboardButton(text="自定义 / Custom", callback_data="topup:custom")
            ],
            [
                InlineKeyboardButton(text=t(lang, "back_menu"), callback_data="menu")
            ],
        ]
    )


def amount_kb(item_id: int, lang: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="50", callback_data=f"buyamt:{item_id}:50"),
                InlineKeyboardButton(text="100", callback_data=f"buyamt:{item_id}:100"),
                InlineKeyboardButton(text="200", callback_data=f"buyamt:{item_id}:200"),
            ],
            [
                InlineKeyboardButton(text="500", callback_data=f"buyamt:{item_id}:500"),
                InlineKeyboardButton(text="1000", callback_data=f"buyamt:{item_id}:1000"),
                InlineKeyboardButton(text="2000", callback_data=f"buyamt:{item_id}:2000"),
            ],
            [
                InlineKeyboardButton(text="自定义 / Custom", callback_data=f"buyamtcustom:{item_id}")
            ],
            [
                InlineKeyboardButton(text=t(lang, "back_menu"), callback_data="menu")
            ],
        ]
    )


def back_to_menu_inline(lang: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "back_menu"), callback_data="menu")]
        ]
    )


def category_name(row, lang):
    return row["name_en"] if lang == "en" else row["name_zh"]


def service_desc(row, lang):
    return row["desc_en"] if lang == "en" else row["desc_zh"]


def premium_prefix(title: str):
    if any(x in title for x in ["Private", "Anonymous", "888", "+"]):
        return "👑 "
    if any(x in title for x in ["Bot", "AI", "Suite"]):
        return "🤖 "
    return "✨ "


async def safe_edit(call: CallbackQuery, text: str, reply_markup=None):
    try:
        if getattr(call.message, "text", None):
            await call.message.edit_text(text, reply_markup=reply_markup)
        elif getattr(call.message, "caption", None) is not None:
            await call.message.edit_caption(caption=text, reply_markup=reply_markup)
        else:
            await call.message.answer(text, reply_markup=reply_markup)
    except TelegramBadRequest as e:
        err = str(e).lower()
        if "message is not modified" in err:
            return
        if "there is no text in the message to edit" in err:
            await call.message.answer(text, reply_markup=reply_markup)
            return
        if "message can't be edited" in err:
            await call.message.answer(text, reply_markup=reply_markup)
            return
        if "there is no caption in the message to edit" in err:
            await call.message.answer(text, reply_markup=reply_markup)
            return
        raise


async def find_category_by_name_en(name_en: str):
    rows = await list_categories()
    for row in rows:
        if row["name_en"] == name_en:
            return row
    return None


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


async def send_services_from_category_name(target, lang: str, category_name_en: str, title_key: str, icon: str = "✨"):
    category = await find_category_by_name_en(category_name_en)
    if not category:
        if isinstance(target, Message):
            await target.answer(t(lang, "no_services"))
        else:
            await safe_edit(target, t(lang, "no_services"))
        return

    rows = await list_services_by_category(category["id"])
    if not rows:
        if isinstance(target, Message):
            await target.answer(t(lang, "no_services"))
        else:
            await safe_edit(target, t(lang, "no_services"))
        return

    kb = InlineKeyboardBuilder()
    for row in rows:
        kb.button(
            text=f"{icon} {row['title']} - {float(row['price']):.2f} USDT",
            callback_data=f"service:{row['id']}"
        )
    kb.button(text=t(lang, "back_menu"), callback_data="menu")
    kb.adjust(1)

    if isinstance(target, Message):
        await target.answer(t(lang, title_key), reply_markup=kb.as_markup())
    else:
        await safe_edit(target, t(lang, title_key), reply_markup=kb.as_markup())


async def send_inventory_from_category_name(target, lang: str, category_name_en: str, title_key: str):
    category = await find_category_by_name_en(category_name_en)
    if not category:
        if isinstance(target, Message):
            await target.answer(t(lang, "no_stock"))
        else:
            await safe_edit(target, t(lang, "no_stock"))
        return

    rows = await list_inventory_by_category(category["id"])
    if not rows:
        if isinstance(target, Message):
            await target.answer(t(lang, "no_stock"))
        else:
            await safe_edit(target, t(lang, "no_stock"))
        return

    kb = InlineKeyboardBuilder()
    for row in rows:
        kb.button(
            text=f"{row['title']} ({int(row['stock'])})",
            callback_data=f"item:{row['id']}"
        )
    kb.button(text=t(lang, "back_menu"), callback_data="menu")
    kb.adjust(1)

    if isinstance(target, Message):
        await target.answer(t(lang, title_key), reply_markup=kb.as_markup())
    else:
        await safe_edit(target, t(lang, title_key), reply_markup=kb.as_markup())


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

    title = f"{premium_prefix(row['title'])}{row['title']}"
    await safe_edit(
        call,
        t(
            lang,
            "service_detail",
            title=title,
            badge=row["badge"],
            price=float(row["price"]),
            description=service_desc(row, lang)
        ),
        reply_markup=kb
    )


async def send_services_by_category(call: CallbackQuery, lang: str, category_id: int):
    category = await get_category(category_id)
    if not category:
        await call.answer(t(lang, "no_categories"), show_alert=True)
        return

    rows = await list_services_by_category(category_id)
    if not rows:
        await safe_edit(call, t(lang, "no_services"), reply_markup=back_to_menu_inline(lang))
        return

    kb = InlineKeyboardBuilder()
    for row in rows:
        kb.button(
            text=f"{row['title']} - {float(row['price']):.2f} USDT",
            callback_data=f"service:{row['id']}"
        )
    kb.button(text=t(lang, "back_menu"), callback_data="menu")
    kb.adjust(1)

    await safe_edit(
        call,
        t(lang, "services_title", category=category_name(category, lang)),
        reply_markup=kb.as_markup()
    )


async def send_invoices_list(target, lang: str, tg_id: int):
    rows = await get_user_invoices(tg_id)
    if not rows:
        if isinstance(target, Message):
            await target.answer(t(lang, "invoices_empty"))
        else:
            await safe_edit(target, t(lang, "invoices_empty"))
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
        await safe_edit(target, t(lang, "invoices_title"), reply_markup=kb.as_markup())


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

    await safe_edit(call, text, reply_markup=kb)


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
    await safe_edit(call, t(lang, f"language_updated_{lang}"))
    await call.message.answer(t(lang, "choose_action"), reply_markup=main_menu(lang))
    await call.answer()


@dp.message(lambda m: m.text and match_key(m.text, "btn_ads"))
async def menu_ads(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)
    await send_services_from_category_name(message, lang, "Broadcast & Advertising", "ads_title", "📢")


@dp.message(lambda m: m.text and match_key(m.text, "btn_cart_menu"))
async def menu_cart_area(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)
    await message.answer(t(lang, "menu_cart_title"), reply_markup=cart_menu(lang))


@dp.message(lambda m: m.text and match_key(m.text, "btn_topup"))
async def menu_topup(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)
    await message.answer(t(lang, "topup_title"), reply_markup=topup_kb(lang))


@dp.message(lambda m: m.text and match_key(m.text, "btn_catalog"))
async def menu_all_services(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)
    await message.answer(t(lang, "menu_services_title"), reply_markup=services_menu(lang))


@dp.message(lambda m: m.text and match_key(m.text, "btn_support"))
async def menu_support(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)
    await message.answer(t(lang, "support_text"), reply_markup=support_kb(lang))


@dp.message(lambda m: m.text and match_key(m.text, "btn_back"))
async def back_main(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)
    await message.answer(t(lang, "choose_action"), reply_markup=main_menu(lang))


@dp.message(lambda m: m.text and match_key(m.text, "btn_anon"))
async def menu_anon(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)
    await send_inventory_from_category_name(message, lang, "Nice Numbers & Anonymous", "anon_title")


@dp.message(lambda m: m.text and match_key(m.text, "btn_vip_bot"))
async def menu_vip_bot(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)
    await send_services_from_category_name(message, lang, "VIP Bot Suites", "vip_bot_title", "🤖")


@dp.message(lambda m: m.text and match_key(m.text, "btn_stars"))
async def menu_stars(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)
    await send_services_from_category_name(message, lang, "Stars Services", "stars_title", "⭐")


@dp.message(lambda m: m.text and match_key(m.text, "btn_premium"))
async def menu_premium(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)
    await send_services_from_category_name(message, lang, "Premium Services", "premium_title", "⭐")


@dp.message(lambda m: m.text and match_key(m.text, "btn_gifts"))
async def menu_gifts(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)
    await send_services_from_category_name(message, lang, "Gifts", "gifts_title", "🎁")


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


@dp.message(lambda m: m.text and match_key(m.text, "btn_fast_broadcast"))
async def menu_fast_broadcast(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)
    await send_services_from_category_name(message, lang, "Broadcast & Advertising", "broadcast_title", "⚡")


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


@dp.callback_query(F.data == "menu"))
async def cb_menu(call: CallbackQuery):
    lang = await get_user_lang(call.from_user.id)
    await call.message.answer(t(lang, "choose_action"), reply_markup=main_menu(lang))
    await call.answer()
@dp.callback_query(F.data == "menu")
async def cb_menu(call: CallbackQuery):
    lang = await get_user_lang(call.from_user.id)
    await call.message.answer(t(lang, "choose_action"), reply_markup=main_menu(lang))
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
async def cb_topup(call: CallbackQuery, state: FSMContext):
    lang = await get_user_lang(call.from_user.id)
    amount_raw = call.data.split(":")[1]

    if amount_raw == "custom":
        await state.set_state(AmountFSM.waiting_custom_topup)
        await call.message.answer(t(lang, "custom_amount_prompt_topup"))
        await call.answer()
        return

    amount = float(amount_raw)
    row = await create_topup_request(call.from_user.id, amount)

    await call.message.answer(
        t(
            lang,
            "topup_created",
            invoice_id=row["id"],
            amount=float(row["amount"]),
            payment_text=PAYMENT_TEXT
        ),
        parse_mode="HTML"
    )

    if ADMIN_ID:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=t(lang, "btn_confirm_topup"), callback_data=f"admin_confirm_topup:{row['id']}")]
            ]
        )
        await bot.send_message(
            ADMIN_ID,
            t(
                lang,
                "admin_topup_notice",
                name=call.from_user.full_name,
                user_id=call.from_user.id,
                amount=float(row["amount"]),
                invoice_id=row["id"]
            ),
            reply_markup=kb
        )

    await call.answer()


@dp.message(AmountFSM.waiting_custom_topup)
async def custom_topup_amount(message: Message, state: FSMContext):
    lang = await get_user_lang(message.from_user.id)
    try:
        amount = float((message.text or "").strip())
        if amount <= 0:
            raise ValueError
    except Exception:
        await message.answer(t(lang, "invalid_amount"))
        return

    row = await create_topup_request(message.from_user.id, amount)
    await message.answer(
        t(
            lang,
            "topup_created",
            invoice_id=row["id"],
            amount=float(row["amount"]),
            payment_text=PAYMENT_TEXT
        ),
        parse_mode="HTML"
    )

    if ADMIN_ID:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=t(lang, "btn_confirm_topup"), callback_data=f"admin_confirm_topup:{row['id']}")]
            ]
        )
        await bot.send_message(
            ADMIN_ID,
            t(
                lang,
                "admin_topup_notice",
                name=message.from_user.full_name,
                user_id=message.from_user.id,
                amount=float(row["amount"]),
                invoice_id=row["id"]
            ),
            reply_markup=kb
        )

    await state.clear()


@dp.callback_query(F.data.startswith("item:"))
async def cb_item(call: CallbackQuery):
    lang = await get_user_lang(call.from_user.id)
    item_id = int(call.data.split(":")[1])
    item = await get_inventory_item(item_id)

    if not item:
        await call.answer(t(lang, "item_not_found"), show_alert=True)
        return

    if int(item["stock"]) <= 0:
        await call.answer(t(lang, "stock_empty"), show_alert=True)
        return

    await call.message.answer(
        f"{item['title']} ({int(item['stock'])})\n\n{t(lang, 'choose_amount')}",
        reply_markup=amount_kb(item_id, lang)
    )
    await call.answer()


@dp.callback_query(F.data.startswith("buyamt:"))
async def cb_buy_amount(call: CallbackQuery):
    lang = await get_user_lang(call.from_user.id)
    _, item_id, amount_raw = call.data.split(":")
    amount = float(amount_raw)

    row = await create_purchase_request(call.from_user.id, int(item_id), amount)
    if not row:
        await call.answer(t(lang, "stock_empty"), show_alert=True)
        return

    await call.message.answer(
        t(
            lang,
            "purchase_created",
            invoice_id=row["id"],
            item=row["item_title"],
            amount=float(row["amount"]),
            payment_text=PAYMENT_TEXT
        ),
        parse_mode="HTML"
    )

    if ADMIN_ID:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=t(lang, "btn_confirm_purchase"), callback_data=f"admin_confirm_purchase:{row['id']}")]
            ]
        )
        await bot.send_message(
            ADMIN_ID,
            t(
                lang,
                "admin_purchase_notice",
                name=call.from_user.full_name,
                user_id=call.from_user.id,
                item=row["item_title"],
                amount=float(row["amount"]),
                invoice_id=row["id"]
            ),
            reply_markup=kb
        )

    await call.answer()


@dp.callback_query(F.data.startswith("buyamtcustom:"))
async def cb_buy_amount_custom(call: CallbackQuery, state: FSMContext):
    lang = await get_user_lang(call.from_user.id)
    item_id = int(call.data.split(":")[1])
    await state.update_data(custom_purchase_item_id=item_id)
    await state.set_state(AmountFSM.waiting_custom_purchase)
    await call.message.answer(t(lang, "custom_amount_prompt_purchase"))
    await call.answer()


@dp.message(AmountFSM.waiting_custom_purchase)
async def custom_purchase_amount(message: Message, state: FSMContext):
    lang = await get_user_lang(message.from_user.id)
    data = await state.get_data()
    item_id = data.get("custom_purchase_item_id")

    if not item_id:
        await state.clear()
        return await message.answer(t(lang, "item_not_found"))

    try:
        amount = float((message.text or "").strip())
        if amount <= 0:
            raise ValueError
    except Exception:
        await message.answer(t(lang, "invalid_amount"))
        return

    row = await create_purchase_request(message.from_user.id, int(item_id), amount)
    if not row:
        await state.clear()
        return await message.answer(t(lang, "stock_empty"))

    await message.answer(
        t(
            lang,
            "purchase_created",
            invoice_id=row["id"],
            item=row["item_title"],
            amount=float(row["amount"]),
            payment_text=PAYMENT_TEXT
        ),
        parse_mode="HTML"
    )

    if ADMIN_ID:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=t(lang, "btn_confirm_purchase"), callback_data=f"admin_confirm_purchase:{row['id']}")]
            ]
        )
        await bot.send_message(
            ADMIN_ID,
            t(
                lang,
                "admin_purchase_notice",
                name=message.from_user.full_name,
                user_id=message.from_user.id,
                item=row["item_title"],
                amount=float(row["amount"]),
                invoice_id=row["id"]
            ),
            reply_markup=kb
        )

    await state.clear()


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


@dp.callback_query(F.data.startswith("admin_confirm_topup:"))
async def cb_admin_confirm_topup(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return await call.answer("No permission", show_alert=True)

    row = await confirm_topup_request(int(call.data.split(":")[1]))
    if not row:
        return await call.answer("Invalid request", show_alert=True)

    await bot.send_message(
        row["telegram_id"],
        t("zh", "topup_confirmed", amount=float(row["amount"]))
    )
    await call.message.answer(f"✅ 已确认充值 #{row['id']}")
    await call.answer()


@dp.callback_query(F.data.startswith("admin_confirm_purchase:"))
async def cb_admin_confirm_purchase(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return await call.answer("No permission", show_alert=True)

    result = await confirm_purchase_request(int(call.data.split(":")[1]))
    if result is False:
        return await call.answer("Out of stock", show_alert=True)
    if not result:
        return await call.answer("Invalid request", show_alert=True)

    await bot.send_message(
        result["telegram_id"],
        t("zh", "purchase_confirmed", item=result["item_title"])
    )
    await call.message.answer(f"✅ 已确认发货 #{result['id']}")
    await call.answer()


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
        featured = val == "1"
        await set_featured(int(service_id), featured)
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


async def main():
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    print("Bot is running...")
    try:
        await dp.start_polling(bot)
    finally:
        await close_db()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

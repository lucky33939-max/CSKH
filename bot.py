import os
import asyncio
from dotenv import load_dotenv
import asyncpg

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

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@your_support")
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/your_channel")
START_BANNER_URL = os.getenv("START_BANNER_URL", "")
PAYMENT_TEXT = os.getenv(
    "PAYMENT_TEXT",
    "USDT TRC20\nWallet: YOUR_WALLET\nAfter payment, send receipt to support."
)
SHOP_NAME = os.getenv("SHOP_NAME", "Telegram Service Hub")

if not BOT_TOKEN:
    raise ValueError("Thiếu BOT_TOKEN")
if not DATABASE_URL:
    raise ValueError("Thiếu DATABASE_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db_pool = None


# =========================
# TRANSLATIONS
# =========================

TRANSLATIONS = {
    "vi": {
        "welcome": f"🔥 Chào mừng đến với {SHOP_NAME}\n\n"
                   "✅ Dịch vụ Telegram chuyên nghiệp\n"
                   "✅ Giao nhanh - hỗ trợ nhanh\n"
                   "✅ Phù hợp quảng bá, vận hành, tự động hóa hợp pháp\n\n"
                   "🎁 Ưu đãi hôm nay đang mở\n"
                   "👇 Chọn chức năng bên dưới để bắt đầu",
        "choose_action": "Chọn chức năng bên dưới:",
        "btn_hot": "🔥 Dịch vụ hot",
        "btn_catalog": "🛍 Danh mục",
        "btn_promo": "💎 Khuyến mãi",
        "btn_topup": "💳 Nạp tiền",
        "btn_balance": "💰 Số dư",
        "btn_orders": "📦 Đơn hàng",
        "btn_language": "🌍 Ngôn ngữ",
        "btn_support": "🆘 Hỗ trợ",
        "btn_channel": "📢 Kênh",
        "btn_center": "👤 Trung tâm",

        "language_title": "🌍 Vui lòng chọn ngôn ngữ:",
        "language_updated_vi": "✅ Đã chuyển sang Tiếng Việt.",
        "language_updated_en": "✅ Language changed to English.",
        "language_updated_zh": "✅ 已切换为中文。",

        "back": "⬅️ Quay lại",
        "back_menu": "🏠 Về menu",
        "view_services": "📂 Xem dịch vụ",
        "buy_now": "🛒 Đặt mua",
        "contact_support": "🆘 Liên hệ hỗ trợ",
        "open_channel": "📢 Vào kênh",
        "topup_now": "💳 Nạp tiền ngay",

        "hot_title": "🔥 Dịch vụ nổi bật\n\nChọn một gói bên dưới:",
        "catalog_title": "🛍 Danh mục dịch vụ\n\nVui lòng chọn danh mục:",
        "services_title": "📂 {category}\n\nChọn dịch vụ bạn muốn xem:",
        "service_detail": (
            "✨ {title}\n"
            "🏷 {badge}\n"
            "💵 Giá: {price:.2f} USDT\n\n"
            "{description}\n\n"
            "📌 Sau khi thanh toán, admin sẽ xử lý đơn và hỗ trợ triển khai."
        ),

        "promo_title": "💎 Ưu đãi hôm nay\n\n{promo}",
        "default_promo": (
            "🎁 Nạp từ 100 USDT: thưởng 5%\n"
            "🎁 Nạp từ 300 USDT: thưởng 10%\n"
            "🎁 Một số gói dịch vụ đang giảm giá giới hạn"
        ),

        "balance_text": "💰 Số dư hiện tại: {balance:.2f} USDT",
        "balance_not_enough": "Số dư không đủ. Vui lòng nạp thêm để tiếp tục.",
        "buy_success": (
            "✅ Tạo đơn thành công\n\n"
            "📦 Dịch vụ: {title}\n"
            "💵 Giá: {price:.2f} USDT\n"
            "🧾 Mã đơn: #{order_id}\n\n"
            "Admin sẽ xử lý và liên hệ bạn sớm."
        ),

        "orders_empty": "Bạn chưa có đơn hàng nào.",
        "orders_title": "📦 10 đơn gần nhất của bạn:\n\n",
        "orders_line": "#{id} - {title} - {price:.2f} USDT - {status} - {created_at}\n",

        "center_text": (
            "🌞 Xin chào, {name}\n\n"
            "🆔 User ID: {user_id}\n"
            "📅 Đăng ký: {created_at}\n"
            "💰 Số dư: {balance:.2f} USDT\n"
            "💸 Tổng chi: {spent:.2f} USDT\n"
            "📦 Tổng đơn: {orders}\n\n"
            "Vui lòng chọn chức năng bên dưới."
        ),

        "support_text": (
            "🆘 Hỗ trợ khách hàng\n\n"
            f"• Support: {SUPPORT_USERNAME}\n"
            f"• Channel: {CHANNEL_URL}\n\n"
            "Nếu bạn cần tư vấn dịch vụ hoặc xác nhận thanh toán, hãy liên hệ hỗ trợ."
        ),

        "channel_text": "📢 Kênh chính thức của shop:",
        "topup_title": "💳 Nạp tiền\n\nChọn mệnh giá hoặc liên hệ hỗ trợ sau khi thanh toán.",
        "topup_info": (
            "💳 Hướng dẫn nạp {amount} USDT\n\n"
            "{payment_text}\n\n"
            f"🆘 Hỗ trợ: {SUPPORT_USERNAME}\n"
            "📌 Gửi kèm Telegram ID của bạn: {user_id}"
        ),

        "no_categories": "Chưa có danh mục.",
        "no_services": "Chưa có dịch vụ trong danh mục này.",
        "service_not_found": "Không tìm thấy dịch vụ.",
        "admin_only": "Bạn không có quyền dùng lệnh này.",
        "admin_help": (
            "⚙️ Admin commands\n\n"
            "/seed\n"
            "/addcategory tên_vi | name_en | 名称_zh\n"
            "/addservice category_id | title | price | badge | desc_vi | desc_en | desc_zh\n"
            "/feature service_id | 1 hoặc 0\n"
            "/setbalance telegram_id | amount\n"
            "/promo nội dung khuyến mãi\n"
            "/broadcast nội dung\n"
            "/services"
        ),
        "seed_done": "✅ Đã tạo dữ liệu mẫu.",
        "category_added": "✅ Đã thêm danh mục.",
        "service_added": "✅ Đã thêm dịch vụ.",
        "feature_updated": "✅ Đã cập nhật featured.",
        "balance_updated": "✅ Đã cập nhật số dư.",
        "promo_updated": "✅ Đã cập nhật khuyến mãi.",
        "broadcast_done": "✅ Đã gửi broadcast.\nThành công: {ok}\nLỗi: {fail}",
        "services_empty": "Chưa có dịch vụ.",
        "services_admin_title": "📋 Danh sách dịch vụ:\n\n",
        "services_admin_line": "ID {id} | {title} | {price:.2f} USDT | Cat {category_id} | Featured: {featured}\n",

        "bad_addcategory": "Sai cú pháp.\nVí dụ:\n/addcategory Dịch vụ Bot | Bot Services | 机器人服务",
        "bad_addservice": "Sai cú pháp.\nVí dụ:\n/addservice 1 | Bot thuê tháng | 49 | HOT | Mô tả VI | English desc | 中文描述",
        "bad_feature": "Sai cú pháp.\nVí dụ:\n/feature 1 | 1",
        "bad_setbalance": "Sai cú pháp.\nVí dụ:\n/setbalance 123456789 | 100",
    },

    "en": {
        "welcome": f"🔥 Welcome to {SHOP_NAME}\n\n"
                   "✅ Professional Telegram services\n"
                   "✅ Fast delivery - fast support\n"
                   "✅ Legal automation and community solutions\n\n"
                   "🎁 Today’s deals are live\n"
                   "👇 Choose an option below to begin",
        "choose_action": "Choose an option below:",
        "btn_hot": "🔥 Hot Services",
        "btn_catalog": "🛍 Catalog",
        "btn_promo": "💎 Promotions",
        "btn_topup": "💳 Top Up",
        "btn_balance": "💰 Balance",
        "btn_orders": "📦 Orders",
        "btn_language": "🌍 Language",
        "btn_support": "🆘 Support",
        "btn_channel": "📢 Channel",
        "btn_center": "👤 My Center",

        "language_title": "🌍 Please choose your language:",
        "language_updated_vi": "✅ Đã chuyển sang Tiếng Việt.",
        "language_updated_en": "✅ Language changed to English.",
        "language_updated_zh": "✅ 已切换为中文。",

        "back": "⬅️ Back",
        "back_menu": "🏠 Main Menu",
        "view_services": "📂 View Services",
        "buy_now": "🛒 Buy Now",
        "contact_support": "🆘 Contact Support",
        "open_channel": "📢 Open Channel",
        "topup_now": "💳 Top Up Now",

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
            "🆘 Customer support\n\n"
            f"• Support: {SUPPORT_USERNAME}\n"
            f"• Channel: {CHANNEL_URL}\n\n"
            "If you need service consultation or payment confirmation, please contact support."
        ),

        "channel_text": "📢 Official channel of the shop:",
        "topup_title": "💳 Top Up\n\nChoose an amount or contact support after payment.",
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
            "/addcategory name_vi | name_en | 名称_zh\n"
            "/addservice category_id | title | price | badge | desc_vi | desc_en | desc_zh\n"
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

        "bad_addcategory": "Wrong syntax.\nExample:\n/addcategory Dịch vụ Bot | Bot Services | 机器人服务",
        "bad_addservice": "Wrong syntax.\nExample:\n/addservice 1 | Monthly Bot Rental | 49 | HOT | Mô tả VI | English desc | 中文描述",
        "bad_feature": "Wrong syntax.\nExample:\n/feature 1 | 1",
        "bad_setbalance": "Wrong syntax.\nExample:\n/setbalance 123456789 | 100",
    },

    "zh": {
        "welcome": f"🔥 欢迎来到 {SHOP_NAME}\n\n"
                   "✅ 专业 Telegram 服务\n"
                   "✅ 交付快速 - 支持快速\n"
                   "✅ 合法自动化与社区解决方案\n\n"
                   "🎁 今日优惠已开启\n"
                   "👇 请选择下面的功能开始",
        "choose_action": "请选择下面的功能：",
        "btn_hot": "🔥 热门服务",
        "btn_catalog": "🛍 服务目录",
        "btn_promo": "💎 优惠活动",
        "btn_topup": "💳 充值",
        "btn_balance": "💰 余额",
        "btn_orders": "📦 订单",
        "btn_language": "🌍 语言",
        "btn_support": "🆘 客服",
        "btn_channel": "📢 频道",
        "btn_center": "👤 个人中心",

        "language_title": "🌍 请选择语言：",
        "language_updated_vi": "✅ Đã chuyển sang Tiếng Việt.",
        "language_updated_en": "✅ Language changed to English.",
        "language_updated_zh": "✅ 已切换为中文。",

        "back": "⬅️ 返回",
        "back_menu": "🏠 主菜单",
        "view_services": "📂 查看服务",
        "buy_now": "🛒 立即购买",
        "contact_support": "🆘 联系客服",
        "open_channel": "📢 打开频道",
        "topup_now": "💳 立即充值",

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
            "如果您需要服务咨询或付款确认，请联系支持。"
        ),

        "channel_text": "📢 商店官方频道：",
        "topup_title": "💳 充值\n\n请选择金额，付款后联系支持。",
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
            "/addcategory 名称_vi | name_en | 名称_zh\n"
            "/addservice category_id | title | price | badge | desc_vi | desc_en | desc_zh\n"
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

        "bad_addcategory": "格式错误。\n例如：\n/addcategory Dịch vụ Bot | Bot Services | 机器人服务",
        "bad_addservice": "格式错误。\n例如：\n/addservice 1 | 月租机器人 | 49 | HOT | Mô tả VI | English desc | 中文描述",
        "bad_feature": "格式错误。\n例如：\n/feature 1 | 1",
        "bad_setbalance": "格式错误。\n例如：\n/setbalance 123456789 | 100",
    }
}


def t(lang: str, key: str, **kwargs):
    lang = lang if lang in TRANSLATIONS else "vi"
    text = TRANSLATIONS[lang].get(key, TRANSLATIONS["vi"].get(key, key))
    return text.format(**kwargs) if kwargs else text


def match_key(text: str, key: str):
    if not text:
        return False
    return text in [TRANSLATIONS[lang][key] for lang in TRANSLATIONS]


# =========================
# KEYBOARDS
# =========================

def main_menu(lang: str):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(lang, "btn_hot")), KeyboardButton(text=t(lang, "btn_catalog"))],
            [KeyboardButton(text=t(lang, "btn_promo")), KeyboardButton(text=t(lang, "btn_topup"))],
            [KeyboardButton(text=t(lang, "btn_balance")), KeyboardButton(text=t(lang, "btn_orders"))],
            [KeyboardButton(text=t(lang, "btn_language")), KeyboardButton(text=t(lang, "btn_support"))],
            [KeyboardButton(text=t(lang, "btn_channel")), KeyboardButton(text=t(lang, "btn_center"))],
        ],
        resize_keyboard=True
    )


def language_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇻🇳 Tiếng Việt", callback_data="lang:vi")],
            [InlineKeyboardButton(text="🇺🇸 English", callback_data="lang:en")],
            [InlineKeyboardButton(text="🇨🇳 中文", callback_data="lang:zh")],
        ]
    )


def back_to_menu_inline(lang: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
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
            [InlineKeyboardButton(text=t(lang, "contact_support"), url=f"https://t.me/{SUPPORT_USERNAME.replace('@','')}")],
            [InlineKeyboardButton(text=t(lang, "back_menu"), callback_data="menu")],
        ]
    )


def support_kb(lang: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "contact_support"), url=f"https://t.me/{SUPPORT_USERNAME.replace('@','')}")],
            [InlineKeyboardButton(text=t(lang, "open_channel"), url=CHANNEL_URL)],
            [InlineKeyboardButton(text=t(lang, "back_menu"), callback_data="menu")],
        ]
    )


# =========================
# DATABASE
# =========================

async def init_db():
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL)

    async with db_pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT UNIQUE NOT NULL,
            username TEXT,
            full_name TEXT,
            language TEXT DEFAULT 'vi',
            balance NUMERIC(12,2) NOT NULL DEFAULT 0,
            total_spent NUMERIC(12,2) NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY,
            name_vi TEXT NOT NULL,
            name_en TEXT NOT NULL,
            name_zh TEXT NOT NULL,
            active BOOLEAN DEFAULT TRUE,
            sort_order INTEGER DEFAULT 0
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id SERIAL PRIMARY KEY,
            category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            price NUMERIC(12,2) NOT NULL DEFAULT 0,
            badge TEXT DEFAULT 'POPULAR',
            desc_vi TEXT DEFAULT '',
            desc_en TEXT DEFAULT '',
            desc_zh TEXT DEFAULT '',
            featured BOOLEAN DEFAULT FALSE,
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT NOT NULL,
            service_id INTEGER NOT NULL REFERENCES services(id) ON DELETE CASCADE,
            price NUMERIC(12,2) NOT NULL,
            status TEXT DEFAULT 'paid',
            created_at TIMESTAMP DEFAULT NOW()
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """)


async def get_or_create_user_from_tg(tg_user):
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT * FROM users WHERE telegram_id = $1",
            tg_user.id
        )
        if not user:
            await conn.execute("""
                INSERT INTO users (telegram_id, username, full_name, language)
                VALUES ($1, $2, $3, 'vi')
            """, tg_user.id, tg_user.username, tg_user.full_name)
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE telegram_id = $1",
                tg_user.id
            )
        return user


async def get_user(tg_id: int):
    async with db_pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM users WHERE telegram_id = $1",
            tg_id
        )


async def get_user_lang(tg_id: int):
    user = await get_user(tg_id)
    return user["language"] if user and user["language"] else "vi"


async def set_user_lang(tg_id: int, lang: str):
    async with db_pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET language = $1 WHERE telegram_id = $2",
            lang, tg_id
        )


async def get_promo_text(lang: str):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT value FROM settings WHERE key = 'promo_text'")
        if row and row["value"]:
            return row["value"]
    return t(lang, "default_promo")


async def list_categories():
    async with db_pool.acquire() as conn:
        return await conn.fetch("""
            SELECT * FROM categories
            WHERE active = TRUE
            ORDER BY sort_order ASC, id ASC
        """)


async def list_featured_services():
    async with db_pool.acquire() as conn:
        return await conn.fetch("""
            SELECT * FROM services
            WHERE active = TRUE AND featured = TRUE
            ORDER BY id ASC
            LIMIT 10
        """)


async def list_services_by_category(category_id: int):
    async with db_pool.acquire() as conn:
        return await conn.fetch("""
            SELECT * FROM services
            WHERE active = TRUE AND category_id = $1
            ORDER BY id ASC
        """, category_id)


async def get_category(category_id: int):
    async with db_pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM categories WHERE id = $1", category_id)


async def get_service(service_id: int):
    async with db_pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM services WHERE id = $1 AND active = TRUE", service_id)


async def create_order(user_tg_id: int, service_id: int):
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE telegram_id = $1 FOR UPDATE",
                user_tg_id
            )
            service = await conn.fetchrow(
                "SELECT * FROM services WHERE id = $1 AND active = TRUE",
                service_id
            )

            if not user or not service:
                return False, "service_not_found"

            if float(user["balance"]) < float(service["price"]):
                return False, "balance_not_enough"

            await conn.execute("""
                UPDATE users
                SET balance = balance - $1,
                    total_spent = total_spent + $1
                WHERE telegram_id = $2
            """, service["price"], user_tg_id)

            order = await conn.fetchrow("""
                INSERT INTO orders (telegram_id, service_id, price, status)
                VALUES ($1, $2, $3, 'paid')
                RETURNING id
            """, user_tg_id, service_id, service["price"])

            return True, {
                "order_id": order["id"],
                "title": service["title"],
                "price": float(service["price"])
            }


async def user_orders(tg_id: int):
    async with db_pool.acquire() as conn:
        return await conn.fetch("""
            SELECT o.id, s.title, o.price, o.status, o.created_at
            FROM orders o
            JOIN services s ON s.id = o.service_id
            WHERE o.telegram_id = $1
            ORDER BY o.id DESC
            LIMIT 10
        """, tg_id)


async def user_orders_count(tg_id: int):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT COUNT(*) AS total FROM orders WHERE telegram_id = $1",
            tg_id
        )
        return int(row["total"]) if row else 0


async def all_user_ids():
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT telegram_id FROM users")
        return [r["telegram_id"] for r in rows]


# =========================
# UI HELPERS
# =========================

def category_name(row, lang):
    if lang == "en":
        return row["name_en"]
    if lang == "zh":
        return row["name_zh"]
    return row["name_vi"]


def service_desc(row, lang):
    if lang == "en":
        return row["desc_en"] or row["desc_vi"] or row["title"]
    if lang == "zh":
        return row["desc_zh"] or row["desc_vi"] or row["title"]
    return row["desc_vi"] or row["title"]


async def send_home(message_or_call, lang: str):
    text = t(lang, "welcome")
    if isinstance(message_or_call, Message):
        if START_BANNER_URL:
            await message_or_call.answer_photo(
                photo=START_BANNER_URL,
                caption=text,
                reply_markup=main_menu(lang)
            )
        else:
            await message_or_call.answer(text, reply_markup=main_menu(lang))
    else:
        await message_or_call.message.answer(text, reply_markup=main_menu(lang))


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

    text = t(lang, "catalog_title")
    if isinstance(target, Message):
        await target.answer(text, reply_markup=kb.as_markup())
    else:
        await target.message.edit_text(text, reply_markup=kb.as_markup())


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

    text = t(lang, "hot_title")
    if isinstance(target, Message):
        await target.answer(text, reply_markup=kb.as_markup())
    else:
        await target.message.edit_text(text, reply_markup=kb.as_markup())


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
            [InlineKeyboardButton(text=t(lang, "contact_support"), url=f"https://t.me/{SUPPORT_USERNAME.replace('@','')}")],
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


# =========================
# USER HANDLERS
# =========================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user = await get_or_create_user_from_tg(message.from_user)
    await send_home(message, user["language"] or "vi")


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
        lang = "vi"

    await set_user_lang(call.from_user.id, lang)

    key = f"language_updated_{lang}"
    await call.message.edit_text(t(lang, key))
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
    await message.answer(
        t(lang, "promo_title", promo=promo),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=t(lang, "topup_now"), callback_data="open_topup")],
                [InlineKeyboardButton(text=t(lang, "back_menu"), callback_data="menu")]
            ]
        )
    )


@dp.message(lambda m: m.text and match_key(m.text, "btn_topup"))
async def menu_topup(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)
    await message.answer(t(lang, "topup_title"), reply_markup=topup_kb(lang))


@dp.message(lambda m: m.text and match_key(m.text, "btn_balance"))
async def menu_balance(message: Message):
    user = await get_or_create_user_from_tg(message.from_user)
    lang = user["language"] or "vi"
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
    lang = user["language"] or "vi"
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
# CALLBACKS
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

    await call.message.answer(
        t(
            lang,
            "buy_success",
            title=result["title"],
            price=result["price"],
            order_id=result["order_id"]
        )
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
async def cb_topup_amount(call: CallbackQuery):
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


# =========================
# ADMIN
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

    async with db_pool.acquire() as conn:
        count = await conn.fetchrow("SELECT COUNT(*) AS total FROM categories")
        if int(count["total"]) == 0:
            await conn.execute("""
                INSERT INTO categories (name_vi, name_en, name_zh, sort_order) VALUES
                ('Thuê Bot', 'Bot Rental', '机器人租用', 1),
                ('Bot Theo Yêu Cầu', 'Custom Bot', '定制机器人', 2),
                ('Setup Group/Channel', 'Group/Channel Setup', '群组/频道搭建', 3),
                ('Telegram Automation', 'Telegram Automation', 'Telegram 自动化', 4),
                ('Premium Gifts', 'Premium Gifts', '高级礼品', 5)
            """)

        svc_count = await conn.fetchrow("SELECT COUNT(*) AS total FROM services")
        if int(svc_count["total"]) == 0:
            await conn.execute("""
                INSERT INTO services
                (category_id, title, price, badge, desc_vi, desc_en, desc_zh, featured)
                VALUES
                (1, 'Bot Thuê Theo Tháng', 49, 'HOT',
                 'Gói bot thuê theo tháng, phù hợp bán hàng, CSKH và marketing Telegram.',
                 'Monthly rental bot package for sales, customer support, and Telegram marketing.',
                 '月租机器人套餐，适合销售、客服和 Telegram 营销。',
                 TRUE),

                (2, 'Bot Đặt Riêng', 129, 'PREMIUM',
                 'Thiết kế bot Telegram theo yêu cầu riêng của doanh nghiệp hoặc cá nhân.',
                 'Custom Telegram bot development based on your business needs.',
                 '根据您的业务需求定制开发 Telegram 机器人。',
                 TRUE),

                (3, 'Setup Group/Channel Pro', 39, 'POPULAR',
                 'Tối ưu group/channel, menu, rule, auto welcome và bố cục chuyên nghiệp.',
                 'Professional setup for group/channel with menu, rules, welcome flow and optimization.',
                 '专业搭建群组/频道，包含菜单、规则、欢迎流程和优化。',
                 TRUE),

                (4, 'Automation Package', 79, 'AUTO',
                 'Tự động hóa tác vụ Telegram hợp pháp: phản hồi, form, điều hướng, mini CRM.',
                 'Legal Telegram automation: replies, forms, routing, mini CRM.',
                 '合法 Telegram 自动化：回复、表单、分流、迷你 CRM。',
                 FALSE),

                (5, 'Premium Gift Assistance', 25, 'GIFT',
                 'Hỗ trợ tư vấn và xử lý gói quà tặng/premium gift hợp lệ.',
                 'Support and consultation for valid premium gift related services.',
                 '提供合法高级礼品相关服务的支持与咨询。',
                 FALSE)
            """)

    await message.answer(t(lang, "seed_done"))


@dp.message(Command("addcategory"))
async def cmd_addcategory(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)
    if not is_admin(message.from_user.id):
        return await message.answer(t(lang, "admin_only"))

    try:
        raw = message.text.replace("/addcategory", "", 1).strip()
        name_vi, name_en, name_zh = [x.strip() for x in raw.split("|", 2)]

        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO categories (name_vi, name_en, name_zh)
                VALUES ($1, $2, $3)
            """, name_vi, name_en, name_zh)

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
        parts = [x.strip() for x in raw.split("|", 6)]

        category_id = int(parts[0])
        title = parts[1]
        price = float(parts[2])
        badge = parts[3]
        desc_vi = parts[4]
        desc_en = parts[5]
        desc_zh = parts[6]

        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO services
                (category_id, title, price, badge, desc_vi, desc_en, desc_zh)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, category_id, title, price, badge, desc_vi, desc_en, desc_zh)

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

        async with db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE services
                SET featured = $1
                WHERE id = $2
            """, featured, int(service_id))

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

        async with db_pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE telegram_id = $1",
                int(tg_id)
            )
            if user:
                await conn.execute("""
                    UPDATE users SET balance = $1 WHERE telegram_id = $2
                """, float(amount), int(tg_id))
            else:
                await conn.execute("""
                    INSERT INTO users (telegram_id, username, full_name, balance, language)
                    VALUES ($1, '', '', $2, 'vi')
                """, int(tg_id), float(amount))

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

    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO settings (key, value)
            VALUES ('promo_text', $1)
            ON CONFLICT (key)
            DO UPDATE SET value = EXCLUDED.value
        """, promo_text)

    await message.answer(t(lang, "promo_updated"))


@dp.message(Command("services"))
async def cmd_services(message: Message):
    await get_or_create_user_from_tg(message.from_user)
    lang = await get_user_lang(message.from_user.id)
    if not is_admin(message.from_user.id):
        return await message.answer(t(lang, "admin_only"))

    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, category_id, title, price, featured
            FROM services
            ORDER BY id ASC
        """)

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
        return await message.answer("Broadcast content empty.")

    user_ids = await all_user_ids()
    ok = 0
    fail = 0

    for uid in user_ids:
        try:
            await bot.send_message(uid, content)
            ok += 1
            await asyncio.sleep(0.05)
        except Exception:
            fail += 1

    await message.answer(t(lang, "broadcast_done", ok=ok, fail=fail))


# =========================
# STARTUP
# =========================

async def main():
    await init_db()
    print("Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
Mình sẽ thay trực tiếp vào code cho bạn.

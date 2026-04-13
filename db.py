import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
PAYMENT_WALLET = os.getenv("PAYMENT_WALLET", "YOUR_USDT_TRC20_WALLET")

if not DATABASE_URL:
    raise ValueError("Missing DATABASE_URL")

db_pool = None

DEFAULT_PROMOS = {
    "en": (
        "🎁 Top up 100 USDT: get 5% bonus\n"
        "🎁 Top up 300 USDT: get 10% bonus\n"
        "🎁 Selected service packages are on limited discount"
    ),
    "zh": (
        "🎁 充值 100 USDT：赠送 5%\n"
        "🎁 充值 300 USDT：赠送 10%\n"
        "🎁 部分服务套餐限时优惠中"
    )
}


async def init_db():
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL)
    print("DB connected")

    async with db_pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT UNIQUE NOT NULL,
            username TEXT,
            full_name TEXT,
            language TEXT DEFAULT 'zh',
            balance NUMERIC(12,2) NOT NULL DEFAULT 0,
            total_spent NUMERIC(12,2) NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """)
        print("users table ready")

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY,
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

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS inventory_items (
            id SERIAL PRIMARY KEY,
            category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0,
            active BOOLEAN DEFAULT TRUE,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS topup_requests (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT NOT NULL,
            amount NUMERIC(12,2) NOT NULL,
            wallet_address TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT NOW(),
            confirmed_at TIMESTAMP
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS purchase_requests (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT NOT NULL,
            item_id INTEGER NOT NULL REFERENCES inventory_items(id) ON DELETE CASCADE,
            item_title TEXT NOT NULL,
            amount NUMERIC(12,2) NOT NULL,
            wallet_address TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT NOW(),
            confirmed_at TIMESTAMP
        );
        """)

        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_id BIGINT;")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS username TEXT;")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name TEXT;")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS language TEXT DEFAULT 'zh';")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS balance NUMERIC(12,2) NOT NULL DEFAULT 0;")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS total_spent NUMERIC(12,2) NOT NULL DEFAULT 0;")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();")

        await conn.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'users_telegram_id_key'
            ) THEN
                ALTER TABLE users
                ADD CONSTRAINT users_telegram_id_key UNIQUE (telegram_id);
            END IF;
        END
        $$;
        """)

        await conn.execute("ALTER TABLE categories ADD COLUMN IF NOT EXISTS name_en TEXT DEFAULT '';")
        await conn.execute("ALTER TABLE categories ADD COLUMN IF NOT EXISTS name_zh TEXT DEFAULT '';")
        await conn.execute("ALTER TABLE categories ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT TRUE;")
        await conn.execute("ALTER TABLE categories ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 0;")

        await conn.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS category_id INTEGER;")
        await conn.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS title TEXT DEFAULT '';")
        await conn.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS price NUMERIC(12,2) NOT NULL DEFAULT 0;")
        await conn.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS badge TEXT DEFAULT 'POPULAR';")
        await conn.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS desc_en TEXT DEFAULT '';")
        await conn.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS desc_zh TEXT DEFAULT '';")
        await conn.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS featured BOOLEAN DEFAULT FALSE;")
        await conn.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT TRUE;")
        await conn.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();")

        await conn.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS telegram_id BIGINT;")
        await conn.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS service_id INTEGER;")
        await conn.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS price NUMERIC(12,2) NOT NULL DEFAULT 0;")
        await conn.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'paid';")
        await conn.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();")

        await conn.execute("ALTER TABLE inventory_items ADD COLUMN IF NOT EXISTS category_id INTEGER;")
        await conn.execute("ALTER TABLE inventory_items ADD COLUMN IF NOT EXISTS title TEXT DEFAULT '';")
        await conn.execute("ALTER TABLE inventory_items ADD COLUMN IF NOT EXISTS stock INTEGER NOT NULL DEFAULT 0;")
        await conn.execute("ALTER TABLE inventory_items ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT TRUE;")
        await conn.execute("ALTER TABLE inventory_items ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 0;")
        await conn.execute("ALTER TABLE inventory_items ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();")

        await conn.execute("ALTER TABLE topup_requests ADD COLUMN IF NOT EXISTS telegram_id BIGINT;")
        await conn.execute("ALTER TABLE topup_requests ADD COLUMN IF NOT EXISTS amount NUMERIC(12,2) NOT NULL DEFAULT 0;")
        await conn.execute("ALTER TABLE topup_requests ADD COLUMN IF NOT EXISTS wallet_address TEXT DEFAULT '';")
        await conn.execute("ALTER TABLE topup_requests ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'pending';")
        await conn.execute("ALTER TABLE topup_requests ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();")
        await conn.execute("ALTER TABLE topup_requests ADD COLUMN IF NOT EXISTS confirmed_at TIMESTAMP;")

        await conn.execute("ALTER TABLE purchase_requests ADD COLUMN IF NOT EXISTS telegram_id BIGINT;")
        await conn.execute("ALTER TABLE purchase_requests ADD COLUMN IF NOT EXISTS item_id INTEGER;")
        await conn.execute("ALTER TABLE purchase_requests ADD COLUMN IF NOT EXISTS item_title TEXT DEFAULT '';")
        await conn.execute("ALTER TABLE purchase_requests ADD COLUMN IF NOT EXISTS amount NUMERIC(12,2) NOT NULL DEFAULT 0;")
        await conn.execute("ALTER TABLE purchase_requests ADD COLUMN IF NOT EXISTS wallet_address TEXT DEFAULT '';")
        await conn.execute("ALTER TABLE purchase_requests ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'pending';")
        await conn.execute("ALTER TABLE purchase_requests ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();")
        await conn.execute("ALTER TABLE purchase_requests ADD COLUMN IF NOT EXISTS confirmed_at TIMESTAMP;")

        await conn.execute("""
            UPDATE users
            SET language = 'zh'
            WHERE language IS NULL OR language = 'vi'
        """)


async def close_db():
    global db_pool
    if db_pool:
        await db_pool.close()
        db_pool = None


async def get_or_create_user_from_tg(tg_user):
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (telegram_id, username, full_name, language)
            VALUES ($1, $2, $3, 'zh')
            ON CONFLICT (telegram_id)
            DO UPDATE SET
                username = EXCLUDED.username,
                full_name = EXCLUDED.full_name
        """, tg_user.id, tg_user.username, tg_user.full_name)

        return await conn.fetchrow(
            "SELECT * FROM users WHERE telegram_id = $1",
            tg_user.id
        )


async def get_user(tg_id: int):
    async with db_pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM users WHERE telegram_id = $1",
            tg_id
        )


async def get_user_lang(tg_id: int):
    user = await get_user(tg_id)
    if not user:
        return "zh"
    return user["language"] or "zh"


async def set_user_lang(tg_id: int, lang: str):
    if lang not in ("en", "zh"):
        lang = "zh"

    async with db_pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET language = $1 WHERE telegram_id = $2",
            lang, tg_id
        )


async def get_promo_text(lang: str):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT value FROM settings WHERE key = 'promo_text'"
        )
        if row and row["value"]:
            return row["value"]

    return DEFAULT_PROMOS.get(lang, DEFAULT_PROMOS["zh"])


async def list_categories():
    async with db_pool.acquire() as conn:
        return await conn.fetch("""
            SELECT * FROM categories
            WHERE active = TRUE
            ORDER BY sort_order ASC, id ASC
        """)


async def get_category(category_id: int):
    async with db_pool.acquire() as conn:
        return await conn.fetchrow("""
            SELECT * FROM categories
            WHERE id = $1
        """, category_id)


async def list_featured_services():
    async with db_pool.acquire() as conn:
        return await conn.fetch("""
            SELECT * FROM services
            WHERE active = TRUE AND featured = TRUE
            ORDER BY id ASC
            LIMIT 20
        """)


async def list_services_by_category(category_id: int):
    async with db_pool.acquire() as conn:
        return await conn.fetch("""
            SELECT * FROM services
            WHERE active = TRUE AND category_id = $1
            ORDER BY id ASC
        """, category_id)


async def get_service(service_id: int):
    async with db_pool.acquire() as conn:
        return await conn.fetchrow("""
            SELECT * FROM services
            WHERE id = $1 AND active = TRUE
        """, service_id)


async def create_order(user_tg_id: int, service_id: int):
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            user = await conn.fetchrow("""
                SELECT * FROM users
                WHERE telegram_id = $1
                FOR UPDATE
            """, user_tg_id)

            service = await conn.fetchrow("""
                SELECT * FROM services
                WHERE id = $1 AND active = TRUE
            """, service_id)

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
                RETURNING id, created_at
            """, user_tg_id, service_id, service["price"])

            return True, {
                "order_id": order["id"],
                "created_at": order["created_at"],
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
        row = await conn.fetchrow("""
            SELECT COUNT(*) AS total
            FROM orders
            WHERE telegram_id = $1
        """, tg_id)
        return int(row["total"]) if row else 0


async def get_user_invoices(tg_id: int):
    async with db_pool.acquire() as conn:
        return await conn.fetch("""
            SELECT o.id, o.price, o.status, o.created_at, s.title
            FROM orders o
            JOIN services s ON s.id = o.service_id
            WHERE o.telegram_id = $1
            ORDER BY o.id DESC
            LIMIT 20
        """, tg_id)


async def get_invoice_by_order_id(order_id: int, tg_id: int):
    async with db_pool.acquire() as conn:
        return await conn.fetchrow("""
            SELECT o.id, o.telegram_id, o.price, o.status, o.created_at, s.title
            FROM orders o
            JOIN services s ON s.id = o.service_id
            WHERE o.id = $1 AND o.telegram_id = $2
        """, order_id, tg_id)


async def all_user_ids():
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT telegram_id FROM users WHERE telegram_id IS NOT NULL")
        return [r["telegram_id"] for r in rows]


async def list_inventory_by_category(category_id: int):
    async with db_pool.acquire() as conn:
        return await conn.fetch("""
            SELECT * FROM inventory_items
            WHERE active = TRUE AND category_id = $1
            ORDER BY sort_order ASC, id ASC
        """, category_id)


async def get_inventory_item(item_id: int):
    async with db_pool.acquire() as conn:
        return await conn.fetchrow("""
            SELECT * FROM inventory_items
            WHERE id = $1 AND active = TRUE
        """, item_id)


async def add_inventory_item(category_id: int, title: str, stock: int, sort_order: int = 0):
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO inventory_items (category_id, title, stock, sort_order, active)
            VALUES ($1, $2, $3, $4, TRUE)
        """, category_id, title, stock, sort_order)


async def create_topup_request(tg_id: int, amount: float, wallet_address: str | None = None):
    wallet = wallet_address or PAYMENT_WALLET
    async with db_pool.acquire() as conn:
        return await conn.fetchrow("""
            INSERT INTO topup_requests (telegram_id, amount, wallet_address, status)
            VALUES ($1, $2, $3, 'pending')
            RETURNING *
        """, tg_id, amount, wallet)


async def confirm_topup_request(request_id: int):
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow("""
                SELECT * FROM topup_requests
                WHERE id = $1
                FOR UPDATE
            """, request_id)

            if not row or row["status"] != "pending":
                return None

            await conn.execute("""
                UPDATE users
                SET balance = balance + $1
                WHERE telegram_id = $2
            """, row["amount"], row["telegram_id"])

            await conn.execute("""
                UPDATE topup_requests
                SET status = 'confirmed',
                    confirmed_at = NOW()
                WHERE id = $1
            """, request_id)

            return row


async def create_purchase_request(tg_id: int, item_id: int, amount: float, wallet_address: str | None = None):
    wallet = wallet_address or PAYMENT_WALLET
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            item = await conn.fetchrow("""
                SELECT * FROM inventory_items
                WHERE id = $1
                FOR UPDATE
            """, item_id)

            if not item or not item["active"] or int(item["stock"]) <= 0:
                return None

            return await conn.fetchrow("""
                INSERT INTO purchase_requests (telegram_id, item_id, item_title, amount, wallet_address, status)
                VALUES ($1, $2, $3, $4, $5, 'pending')
                RETURNING *
            """, tg_id, item_id, item["title"], amount, wallet)


async def confirm_purchase_request(request_id: int):
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow("""
                SELECT * FROM purchase_requests
                WHERE id = $1
                FOR UPDATE
            """, request_id)

            if not row or row["status"] != "pending":
                return None

            item = await conn.fetchrow("""
                SELECT * FROM inventory_items
                WHERE id = $1
                FOR UPDATE
            """, row["item_id"])

            if not item or not item["active"] or int(item["stock"]) <= 0:
                return False

            await conn.execute("""
                UPDATE inventory_items
                SET stock = stock - 1
                WHERE id = $1
            """, row["item_id"])

            await conn.execute("""
                UPDATE purchase_requests
                SET status = 'confirmed',
                    confirmed_at = NOW()
                WHERE id = $1
            """, request_id)

            return row


async def get_topup_request(request_id: int):
    async with db_pool.acquire() as conn:
        return await conn.fetchrow("""
            SELECT * FROM topup_requests WHERE id = $1
        """, request_id)


async def get_purchase_request(request_id: int):
    async with db_pool.acquire() as conn:
        return await conn.fetchrow("""
            SELECT * FROM purchase_requests WHERE id = $1
        """, request_id)


async def seed_sample_data():
    async with db_pool.acquire() as conn:
        count = await conn.fetchrow("SELECT COUNT(*) AS total FROM categories")
        if int(count["total"]) == 0:
            await conn.execute("""
                INSERT INTO categories (name_en, name_zh, sort_order) VALUES
                ('Nice Numbers & Anonymous', '私享号码与匿名号码', 1),
                ('VIP Bot Suites', 'VIP 机器人套件', 2),
                ('Stars Services', 'Stars 服务', 3),
                ('Premium Services', 'Premium 服务', 4),
                ('Gifts', '礼品服务', 5),
                ('Broadcast & Advertising', '广告与快速推送', 6),
                ('AI & Custom Bots', 'AI 与定制机器人', 7)
            """)

        svc_count = await conn.fetchrow("SELECT COUNT(*) AS total FROM services")
        if int(svc_count["total"]) == 0:
            await conn.execute("""
                INSERT INTO services
                (category_id, title, price, badge, desc_en, desc_zh, featured)
                VALUES
                (
                    2, 'Group Management Bot Rental', 49, 'HOT',
                    'Professional group management bot rental package.',
                    '专业群组管理机器人租用套餐。',
                    TRUE
                ),
                (
                    2, 'Calculator Bot Rental', 39, 'TOOLS',
                    'Telegram calculator bot rental.',
                    'Telegram 计算机器人租用。',
                    FALSE
                ),
                (
                    2, 'Translator Bot Rental', 59, 'LANG',
                    'Telegram translator bot rental.',
                    'Telegram 翻译机器人租用。',
                    FALSE
                ),
                (
                    7, 'AI Assistant Bot Rental', 99, 'AI',
                    'AI assistant bot for customer support and automation.',
                    '适用于客服与自动化的 AI 助手机器人。',
                    TRUE
                ),
                (
                    7, 'AI Multi-Tool Bot Pro', 149, 'PRO',
                    'Advanced AI multi-tool Telegram bot.',
                    '高级 AI 多功能 Telegram 机器人。',
                    TRUE
                ),
                (
                    7, 'Custom Bot Development', 199, 'CUSTOM',
                    'Custom Telegram bot development.',
                    '定制 Telegram 机器人开发。',
                    TRUE
                ),
                (
                    6, 'Fast Broadcast Setup (Opt-in Only)', 79, 'FAST',
                    'Fast opt-in broadcast setup support.',
                    '快速合规推送系统搭建支持。',
                    FALSE
                ),
                (
                    6, 'Advertising Placement Support', 59, 'ADS',
                    'Advertising placement support.',
                    '广告投放支持。',
                    FALSE
                ),
                (
                    6, 'Promotional Message Design Support', 35, 'PROMO',
                    'Promotional copy and message design support.',
                    '营销文案与消息设计支持。',
                    FALSE
                ),
                (
                    3, 'Telegram Stars - 500', 50, 'STARS',
                    'Telegram Stars package 500.',
                    'Telegram Stars 500 套餐。',
                    FALSE
                ),
                (
                    3, 'Telegram Stars - 1000', 100, 'STARS',
                    'Telegram Stars package 1000.',
                    'Telegram Stars 1000 套餐。',
                    FALSE
                ),
                (
                    4, 'Telegram Premium VIP - 1 Month', 8, 'VIP',
                    'Telegram Premium VIP 1 month.',
                    'Telegram Premium VIP 一个月。',
                    FALSE
                ),
                (
                    4, 'Telegram Premium VIP - 3 Months', 20, 'VIP',
                    'Telegram Premium VIP 3 months.',
                    'Telegram Premium VIP 三个月。',
                    FALSE
                ),
                (
                    5, 'Telegram Gift Assistance', 25, 'GIFT',
                    'Gift related support and consultation.',
                    '礼品相关支持与咨询。',
                    FALSE
                )
            """)

        inv_count = await conn.fetchrow("SELECT COUNT(*) AS total FROM inventory_items")
        if int(inv_count["total"]) == 0:
            anon_cat = await conn.fetchrow("""
                SELECT id FROM categories WHERE name_en = 'Nice Numbers & Anonymous' LIMIT 1
            """)
            if anon_cat:
                await conn.execute("""
                    INSERT INTO inventory_items (category_id, title, stock, sort_order, active)
                    VALUES
                    ($1, '+111', 5, 1, TRUE),
                    ($1, '+1', 7, 2, TRUE),
                    ($1, '+222', 50, 3, TRUE)
                """, anon_cat["id"])


async def add_category(name_en: str, name_zh: str):
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO categories (name_en, name_zh)
            VALUES ($1, $2)
        """, name_en, name_zh)


async def add_service(category_id: int, title: str, price: float, badge: str, desc_en: str, desc_zh: str):
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO services
            (category_id, title, price, badge, desc_en, desc_zh)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, category_id, title, price, badge, desc_en, desc_zh)


async def set_featured(service_id: int, featured: bool):
    async with db_pool.acquire() as conn:
        await conn.execute("""
            UPDATE services
            SET featured = $1
            WHERE id = $2
        """, featured, service_id)


async def set_balance(tg_id: int, amount: float):
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT * FROM users WHERE telegram_id = $1",
            tg_id
        )

        if user:
            await conn.execute("""
                UPDATE users
                SET balance = $1
                WHERE telegram_id = $2
            """, amount, tg_id)
        else:
            await conn.execute("""
                INSERT INTO users (telegram_id, username, full_name, balance, language)
                VALUES ($1, '', '', $2, 'zh')
            """, tg_id, amount)


async def set_promo_text(promo_text: str):
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO settings (key, value)
            VALUES ('promo_text', $1)
            ON CONFLICT (key)
            DO UPDATE SET value = EXCLUDED.value
        """, promo_text)


async def list_services_admin():
    async with db_pool.acquire() as conn:
        return await conn.fetch("""
            SELECT id, category_id, title, price, featured
            FROM services
            ORDER BY id ASC
        """)

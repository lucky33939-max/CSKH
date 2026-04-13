import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
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

    async with db_pool.acquire() as conn:
        # =========================
        # CREATE TABLES
        # =========================
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

        # =========================
        # SAFE MIGRATIONS - USERS
        # =========================
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_id BIGINT;")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS username TEXT;")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name TEXT;")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS language TEXT DEFAULT 'zh';")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS balance NUMERIC(12,2) NOT NULL DEFAULT 0;")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS total_spent NUMERIC(12,2) NOT NULL DEFAULT 0;")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();")

        # unique constraint for telegram_id
        await conn.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'users_telegram_id_key'
            ) THEN
                ALTER TABLE users
                ADD CONSTRAINT users_telegram_id_key UNIQUE (telegram_id);
            END IF;
        END
        $$;
        """)

        # =========================
        # SAFE MIGRATIONS - CATEGORIES
        # =========================
        await conn.execute("ALTER TABLE categories ADD COLUMN IF NOT EXISTS name_en TEXT DEFAULT '';")
        await conn.execute("ALTER TABLE categories ADD COLUMN IF NOT EXISTS name_zh TEXT DEFAULT '';")
        await conn.execute("ALTER TABLE categories ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT TRUE;")
        await conn.execute("ALTER TABLE categories ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 0;")

        # =========================
        # SAFE MIGRATIONS - SERVICES
        # =========================
        await conn.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS category_id INTEGER;")
        await conn.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS title TEXT DEFAULT '';")
        await conn.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS price NUMERIC(12,2) NOT NULL DEFAULT 0;")
        await conn.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS badge TEXT DEFAULT 'POPULAR';")
        await conn.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS desc_en TEXT DEFAULT '';")
        await conn.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS desc_zh TEXT DEFAULT '';")
        await conn.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS featured BOOLEAN DEFAULT FALSE;")
        await conn.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT TRUE;")
        await conn.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();")

        # =========================
        # SAFE MIGRATIONS - ORDERS
        # =========================
        await conn.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS telegram_id BIGINT;")
        await conn.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS service_id INTEGER;")
        await conn.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS price NUMERIC(12,2) NOT NULL DEFAULT 0;")
        await conn.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'paid';")
        await conn.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();")

        # =========================
        # FIX OLD LANGUAGE VALUES
        # =========================
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
        user = await conn.fetchrow(
            "SELECT * FROM users WHERE telegram_id = $1",
            tg_user.id
        )

        if not user:
            await conn.execute("""
                INSERT INTO users (telegram_id, username, full_name, language)
                VALUES ($1, $2, $3, 'zh')
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


# =========================
# ADMIN HELPERS
# =========================

async def seed_sample_data():
    async with db_pool.acquire() as conn:
        count = await conn.fetchrow("SELECT COUNT(*) AS total FROM categories")
        if int(count["total"]) == 0:
            await conn.execute("""
                INSERT INTO categories (name_en, name_zh, sort_order) VALUES
                ('Bot Rental', '机器人租用', 1),
                ('Custom Bot', '定制机器人', 2),
                ('Group/Channel Setup', '群组/频道搭建', 3),
                ('Telegram Automation', 'Telegram 自动化', 4),
                ('Premium Gifts', '高级礼品', 5)
            """)

        svc_count = await conn.fetchrow("SELECT COUNT(*) AS total FROM services")
        if int(svc_count["total"]) == 0:
            await conn.execute("""
                INSERT INTO services
                (category_id, title, price, badge, desc_en, desc_zh, featured)
                VALUES
                (
                    1, 'Monthly Bot Rental', 49, 'HOT',
                    'Monthly rental bot package for sales, customer support and Telegram marketing.',
                    '月租机器人套餐，适合销售、客服和 Telegram 营销。',
                    TRUE
                ),
                (
                    2, 'Custom Bot Development', 129, 'PREMIUM',
                    'Custom Telegram bot development based on your business needs.',
                    '根据您的业务需求定制开发 Telegram 机器人。',
                    TRUE
                ),
                (
                    3, 'Group/Channel Setup Pro', 39, 'POPULAR',
                    'Professional setup for group/channel with menu, rules, welcome flow and optimization.',
                    '专业搭建群组/频道，包含菜单、规则、欢迎流程和优化。',
                    TRUE
                ),
                (
                    4, 'Automation Package', 79, 'AUTO',
                    'Legal Telegram automation: replies, forms, routing, mini CRM.',
                    '合法 Telegram 自动化：回复、表单、分流、迷你 CRM。',
                    FALSE
                ),
                (
                    5, 'Premium Gift Assistance', 25, 'GIFT',
                    'Support and consultation for valid premium gift related services.',
                    '提供合法高级礼品相关服务的支持与咨询。',
                    FALSE
                )
            """)


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

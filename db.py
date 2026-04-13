import time
from contextlib import contextmanager

import psycopg2
from psycopg2.pool import ThreadedConnectionPool

from config import DATABASE_URL


_pool = ThreadedConnectionPool(1, 10, dsn=DATABASE_URL)


def now_ts():
    return int(time.time())


def get_conn():
    return _pool.getconn()


def put_conn(conn):
    _pool.putconn(conn)


@contextmanager
def get_db(commit=False):
    conn = None
    cur = None
    try:
        conn = get_conn()
        conn.autocommit = not commit
        cur = conn.cursor()
        yield conn, cur
        if commit:
            conn.commit()
    except Exception:
        if conn and commit:
            conn.rollback()
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            put_conn(conn)


def init_db():
    with get_db(commit=True) as (_, cur):
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            balance DOUBLE PRECISION DEFAULT 0,
            created_at BIGINT NOT NULL
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id BIGSERIAL PRIMARY KEY,
            code TEXT UNIQUE,
            title TEXT NOT NULL
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id BIGSERIAL PRIMARY KEY,
            category_id BIGINT REFERENCES categories(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            price DOUBLE PRECISION NOT NULL,
            stock INTEGER DEFAULT 0,
            description TEXT DEFAULT ''
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            product_id BIGINT REFERENCES products(id),
            quantity INTEGER NOT NULL,
            amount DOUBLE PRECISION NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at BIGINT NOT NULL
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS topup_orders (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            amount DOUBLE PRECISION NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at BIGINT NOT NULL
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS topup_tx_claims (
            txid TEXT PRIMARY KEY,
            topup_order_id BIGINT REFERENCES topup_orders(id) ON DELETE CASCADE,
            created_at BIGINT NOT NULL
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS balance_transactions (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            tx_type TEXT NOT NULL,
            amount DOUBLE PRECISION NOT NULL,
            ref_id BIGINT,
            note TEXT DEFAULT '',
            created_at BIGINT NOT NULL
        )
        """)

        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_topup_orders_user_created
        ON topup_orders(user_id, created_at DESC)
        """)

        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_orders_user_created
        ON orders(user_id, created_at DESC)
        """)

        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_category
        ON products(category_id, id ASC)
        """)

        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_balance_tx_user_created
        ON balance_transactions(user_id, created_at DESC)
        """)
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    balance NUMERIC DEFAULT 0
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name TEXT,
    price NUMERIC,
    stock INT DEFAULT 0
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS accounts (
    id SERIAL PRIMARY KEY,
    product_id INT,
    data TEXT,
    is_sold BOOLEAN DEFAULT FALSE
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    product_id INT,
    price NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS payments (
    payment_id TEXT PRIMARY KEY
);
""")

# ================= USERS =================

def upsert_user(user_id, username="", full_name=""):
    with get_db(commit=True) as (_, cur):
        cur.execute("""
        INSERT INTO users(user_id, username, full_name, created_at)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT(user_id) DO UPDATE SET
            username = EXCLUDED.username,
            full_name = EXCLUDED.full_name
        """, (int(user_id), username, full_name, now_ts()))


def get_user(user_id):
    with get_db() as (_, cur):
        cur.execute("""
        SELECT user_id, username, full_name, balance, created_at
        FROM users
        WHERE user_id=%s
        """, (int(user_id),))
        return cur.fetchone()


def get_user_balance(user_id):
    with get_db() as (_, cur):
        cur.execute("""
        SELECT balance
        FROM users
        WHERE user_id=%s
        """, (int(user_id),))
        row = cur.fetchone()
        return float(row[0]) if row else 0.0


# ================= CATEGORIES / PRODUCTS =================

def get_categories():
    with get_db() as (_, cur):
        cur.execute("""
        SELECT id, code, title
        FROM categories
        ORDER BY id ASC
        """)
        return cur.fetchall()


def get_products_by_category(category_id):
    with get_db() as (_, cur):
        cur.execute("""
        SELECT id, title, price, stock, description
        FROM products
        WHERE category_id=%s
        ORDER BY id ASC
        """, (int(category_id),))
        return cur.fetchall()


def get_product(product_id):
    with get_db() as (_, cur):
        cur.execute("""
        SELECT id, category_id, title, price, stock, description
        FROM products
        WHERE id=%s
        """, (int(product_id),))
        return cur.fetchone()


# ================= BALANCE TX =================

def add_balance_transaction(user_id, tx_type, amount, ref_id=None, note=""):
    with get_db(commit=True) as (_, cur):
        cur.execute("""
        INSERT INTO balance_transactions(user_id, tx_type, amount, ref_id, note, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            int(user_id),
            str(tx_type),
            float(amount),
            int(ref_id) if ref_id is not None else None,
            str(note or ""),
            now_ts(),
        ))


def get_user_balance_transactions(user_id, limit=50):
    with get_db() as (_, cur):
        cur.execute("""
        SELECT id, tx_type, amount, ref_id, note, created_at
        FROM balance_transactions
        WHERE user_id=%s
        ORDER BY id DESC
        LIMIT %s
        """, (int(user_id), int(limit)))
        return cur.fetchall()


# ================= ORDERS =================

def create_order(user_id, product_id, quantity, amount, status="pending"):
    with get_db(commit=True) as (_, cur):
        cur.execute("""
        INSERT INTO orders(user_id, product_id, quantity, amount, status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
        """, (
            int(user_id),
            int(product_id),
            int(quantity),
            float(amount),
            str(status),
            now_ts(),
        ))
        return cur.fetchone()[0]


def get_user_orders(user_id):
    with get_db() as (_, cur):
        cur.execute("""
        SELECT o.id, p.title, o.quantity, o.amount, o.status, o.created_at
        FROM orders o
        LEFT JOIN products p ON p.id = o.product_id
        WHERE o.user_id=%s
        ORDER BY o.id DESC
        """, (int(user_id),))
        return cur.fetchall()


def purchase_product(user_id, product_id, quantity):
    qty = int(quantity)
    if qty <= 0:
        return None, "❌ Quantity must be greater than 0"

    with get_db(commit=True) as (_, cur):
        # lock user row
        cur.execute("""
        SELECT user_id, balance
        FROM users
        WHERE user_id=%s
        FOR UPDATE
        """, (int(user_id),))
        user_row = cur.fetchone()

        if not user_row:
            return None, "❌ User not found"

        _, balance = user_row
        balance = float(balance or 0)

        # lock product row
        cur.execute("""
        SELECT id, title, price, stock
        FROM products
        WHERE id=%s
        FOR UPDATE
        """, (int(product_id),))
        product_row = cur.fetchone()

        if not product_row:
            return None, "❌ 商品不存在"

        pid, title, price, stock = product_row
        price = float(price)
        stock = int(stock or 0)

        if qty > stock:
            return None, "❌ Quantity exceeds stock"

        amount = price * qty

        if balance < amount:
            return None, "❌ Insufficient balance"

        # deduct balance
        cur.execute("""
        UPDATE users
        SET balance = COALESCE(balance, 0) - %s
        WHERE user_id=%s
        """, (amount, int(user_id)))

        # deduct stock
        cur.execute("""
        UPDATE products
        SET stock = stock - %s
        WHERE id=%s
        """, (qty, int(product_id)))

        # create order
        cur.execute("""
        INSERT INTO orders(user_id, product_id, quantity, amount, status, created_at)
        VALUES (%s, %s, %s, %s, 'paid', %s)
        RETURNING id
        """, (int(user_id), int(product_id), qty, amount, now_ts()))
        order_id = cur.fetchone()[0]

        # log transaction
        cur.execute("""
        INSERT INTO balance_transactions(user_id, tx_type, amount, ref_id, note, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            int(user_id),
            "purchase",
            -amount,
            int(order_id),
            f"Purchase: {title}",
            now_ts(),
        ))

        return {
            "order_id": order_id,
            "product_id": pid,
            "title": title,
            "price": price,
            "qty": qty,
            "amount": amount,
            "status": "paid",
        }, None


# ================= SAMPLE DATA =================

def seed_sample_data():
    with get_db(commit=True) as (_, cur):
        cur.execute("SELECT COUNT(*) FROM categories")
        if (cur.fetchone() or [0])[0] > 0:
            return

        categories = [
            ("fancy", "✨ Fancy Number"),
            ("country", "🌍 Country / Area Code"),
            ("aged", "💎 Aged Accounts"),
            ("energy", "⚡ Energy Rental"),
        ]

        cat_ids = {}
        for code, title in categories:
            cur.execute("""
            INSERT INTO categories(code, title)
            VALUES (%s, %s)
            RETURNING id
            """, (code, title))
            cat_ids[code] = cur.fetchone()[0]

        products = [
            (cat_ids["fancy"], "Random 5A Fancy Number Ending with Digit 1", 6.62, 8, "All accounts are guaranteed for first-login."),
            (cat_ids["country"], "+84 Vietnam~February-May", 0.95, 85, "Session / API Link available."),
            (cat_ids["country"], "+66 Thailand~February-May", 1.47, 1281, "Session / API Link available."),
            (cat_ids["country"], "+1 USA~February-May", 0.60, 7214, "Session / API Link available."),
            (cat_ids["aged"], "1-2 Year Old Accounts", 9.99, 120, "Suitable for long-term usage."),
            (cat_ids["aged"], "3-4 Year Old Accounts", 19.99, 65, "Higher trust age."),
            (cat_ids["energy"], "TRON Energy Flash Rental", 2.50, 999, "Fast rental for TRX network."),
        ]

        for category_id, title, price, stock, description in products:
            cur.execute("""
            INSERT INTO products(category_id, title, price, stock, description)
            VALUES (%s, %s, %s, %s, %s)
            """, (category_id, title, price, stock, description))


# ================= TOPUP ORDERS =================

def create_topup_order(user_id, amount):
    with get_db(commit=True) as (_, cur):
        cur.execute("""
        INSERT INTO topup_orders(user_id, amount, status, created_at)
        VALUES (%s, %s, 'pending', %s)
        RETURNING id
        """, (int(user_id), float(amount), now_ts()))
        return cur.fetchone()[0]


def get_user_topup_orders(user_id):
    with get_db() as (_, cur):
        cur.execute("""
        SELECT id, amount, status, created_at
        FROM topup_orders
        WHERE user_id=%s
        ORDER BY id DESC
        """, (int(user_id),))
        return cur.fetchall()


def get_topup_order(order_id):
    with get_db() as (_, cur):
        cur.execute("""
        SELECT id, user_id, amount, status, created_at
        FROM topup_orders
        WHERE id=%s
        """, (int(order_id),))
        return cur.fetchone()


def get_topup_orders(status=None, limit=100):
    with get_db() as (_, cur):
        if status:
            cur.execute("""
            SELECT id, user_id, amount, status, created_at
            FROM topup_orders
            WHERE status=%s
            ORDER BY id DESC
            LIMIT %s
            """, (status, int(limit)))
        else:
            cur.execute("""
            SELECT id, user_id, amount, status, created_at
            FROM topup_orders
            ORDER BY id DESC
            LIMIT %s
            """, (int(limit),))
        return cur.fetchall()


def mark_topup_order_paid(order_id):
    with get_db(commit=True) as (_, cur):
        cur.execute("""
        UPDATE topup_orders
        SET status='paid'
        WHERE id=%s
        """, (int(order_id),))


def mark_topup_order_rejected(order_id):
    with get_db(commit=True) as (_, cur):
        cur.execute("""
        UPDATE topup_orders
        SET status='rejected'
        WHERE id=%s
        """, (int(order_id),))


def add_user_balance(user_id, amount):
    with get_db(commit=True) as (_, cur):
        cur.execute("""
        UPDATE users
        SET balance = COALESCE(balance, 0) + %s
        WHERE user_id=%s
        """, (float(amount), int(user_id)))


def approve_topup_order(order_id):
    with get_db(commit=True) as (_, cur):
        # lock topup order
        cur.execute("""
        SELECT id, user_id, amount, status, created_at
        FROM topup_orders
        WHERE id=%s
        FOR UPDATE
        """, (int(order_id),))
        row = cur.fetchone()

        if not row:
            return None, "订单不存在"

        _id, user_id, amount, status, created_at = row
        amount = float(amount)

        if status == "paid":
            return row, "订单已支付"

        if status == "rejected":
            return row, "订单已拒绝"

        # lock user row
        cur.execute("""
        SELECT user_id
        FROM users
        WHERE user_id=%s
        FOR UPDATE
        """, (int(user_id),))
        user_row = cur.fetchone()

        if not user_row:
            return None, "用户不存在"

        # mark paid
        cur.execute("""
        UPDATE topup_orders
        SET status='paid'
        WHERE id=%s
        """, (int(order_id),))

        # add balance
        cur.execute("""
        UPDATE users
        SET balance = COALESCE(balance, 0) + %s
        WHERE user_id=%s
        """, (amount, int(user_id)))

        # log transaction
        cur.execute("""
        INSERT INTO balance_transactions(user_id, tx_type, amount, ref_id, note, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            int(user_id),
            "topup",
            amount,
            int(order_id),
            "Top-up approved",
            now_ts(),
        ))

        return row, None


def claim_topup_tx(txid, topup_order_id):
    with get_db(commit=True) as (_, cur):
        cur.execute("""
        INSERT INTO topup_tx_claims(txid, topup_order_id, created_at)
        VALUES (%s, %s, %s)
        ON CONFLICT(txid) DO NOTHING
        RETURNING txid
        """, (str(txid), int(topup_order_id), now_ts()))
        return cur.fetchone() is not None

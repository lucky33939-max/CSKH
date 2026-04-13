import asyncpg
import asyncio
import os

DATABASE_URL = os.getenv("DATABASE_URL")

db_pool = None


# =========================
# CONNECT DB (AUTO RETRY + CREATE TABLE)
# =========================
async def init_db():
    global db_pool

    while True:
        try:
            db_pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=1,
                max_size=5,
                max_inactive_connection_lifetime=30,
            )

            print("✅ DB Connected")

            # 👉 tạo table luôn (QUAN TRỌNG)
            async with db_pool.acquire() as conn:
                await conn.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    product_type TEXT,
                    product_id TEXT,
                    amount NUMERIC,
                    status TEXT DEFAULT 'pending',
                    delivered BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                """)

            print("✅ Table ready")

            break

        except Exception as e:
            print("❌ DB FAIL, retry...", e)
            await asyncio.sleep(5)


# =========================
# KEEP DB ALIVE
# =========================
async def keep_db_alive():
    while True:
        try:
            async with db_pool.acquire() as conn:
                await conn.execute("SELECT 1")
            print("💓 DB alive")
        except Exception as e:
            print("⚠️ DB reconnecting...", e)
            await init_db()

        await asyncio.sleep(20)


# =========================
# SAFE EXECUTE
# =========================
async def execute(query, *args):
    for _ in range(3):
        try:
            async with db_pool.acquire() as conn:
                return await conn.execute(query, *args)
        except Exception as e:
            print("❌ DB EXEC ERROR:", e)
            await asyncio.sleep(1)


# =========================
# SAFE FETCH ONE
# =========================
async def fetchrow(query, *args):
    for _ in range(3):
        try:
            async with db_pool.acquire() as conn:
                return await conn.fetchrow(query, *args)
        except Exception as e:
            print("❌ DB FETCHROW ERROR:", e)
            await asyncio.sleep(1)


# =========================
# SAFE FETCH ALL
# =========================
async def fetch(query, *args):
    for _ in range(3):
        try:
            async with db_pool.acquire() as conn:
                return await conn.fetch(query, *args)
        except Exception as e:
            print("❌ DB FETCH ERROR:", e)
            await asyncio.sleep(1)

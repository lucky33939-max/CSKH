import asyncpg
import asyncio
import os
import logging

DATABASE_URL = os.getenv("DATABASE_URL")


class DB:
    pool = None
    lock = asyncio.Lock()  # 🔥 chống race condition


# =========================
# INIT DB (SAFE)
# =========================
async def init_db():
    async with DB.lock:  # 🔥 đảm bảo chỉ init 1 lần
        if DB.pool:
            return

        while True:
            try:
                DB.pool = await asyncpg.create_pool(
                    DATABASE_URL,
                    min_size=1,
                    max_size=5,
                    max_inactive_connection_lifetime=30,
                )

                logging.info("✅ DB Connected")

                # 🔥 CREATE TABLES
                async with DB.pool.acquire() as conn:
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

                    await conn.execute("""
                    CREATE TABLE IF NOT EXISTS products (
                        id SERIAL PRIMARY KEY,
                        type TEXT,
                        value TEXT,
                        is_sold BOOLEAN DEFAULT FALSE
                    );
                    """)

                logging.info("✅ Tables ready")
                break

            except Exception as e:
                logging.error(f"❌ DB FAIL: {e}")
                await asyncio.sleep(5)


# =========================
# KEEP ALIVE
# =========================
async def keep_db_alive():
    while True:
        try:
            async with DB.pool.acquire() as conn:
                await conn.execute("SELECT 1")
        except Exception as e:
            logging.warning(f"⚠️ Reconnecting DB: {e}")
            DB.pool = None
            await init_db()

        await asyncio.sleep(60)


# =========================
# SAFE EXECUTE
# =========================
async def execute(query, *args):
    for _ in range(3):
        try:
            async with DB.pool.acquire() as conn:
                return await conn.execute(query, *args)
        except Exception as e:
            logging.error(f"DB EXEC ERROR: {e}")
            DB.pool = None
            await init_db()
    return None


# =========================
# SAFE FETCH ONE
# =========================
async def fetchrow(query, *args):
    for _ in range(3):
        try:
            async with DB.pool.acquire() as conn:
                return await conn.fetchrow(query, *args)
        except Exception as e:
            logging.error(f"DB FETCHROW ERROR: {e}")
            DB.pool = None
            await init_db()
    return None


# =========================
# SAFE FETCH ALL
# =========================
async def fetch(query, *args):
    for _ in range(3):
        try:
            async with DB.pool.acquire() as conn:
                return await conn.fetch(query, *args)
        except Exception as e:
            logging.error(f"DB FETCH ERROR: {e}")
            DB.pool = None
            await init_db()
    return []

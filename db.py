import time
from contextlib import contextmanager
from psycopg2.pool import ThreadedConnectionPool
from config import DATABASE_URL

_pool = None


def now_ts():
    return int(time.time())


def get_pool():
    global _pool
    if _pool is None:
        _pool = ThreadedConnectionPool(1, 10, dsn=DATABASE_URL)
    return _pool


def get_conn():
    return get_pool().getconn()


def put_conn(conn):
    get_pool().putconn(conn)


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

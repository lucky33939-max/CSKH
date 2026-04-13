from fastapi import FastAPI
from db import cursor

app = FastAPI()

@app.get("/stats")
def stats():
    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(price) FROM products")
    revenue = cursor.fetchone()[0] or 0

    return {
        "users": users,
        "revenue": revenue
    }

import sqlite3
import os
from datetime import datetime
import pytz

DB_FILE = "/home/coconut/stockengine/data/stocks.db"
IST     = pytz.timezone("Asia/Kolkata")

# ── Create database and table ─────────────────────────────
def init_db():
    # Create data folder if not exists
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)

    conn = sqlite3.connect(DB_FILE)
    c    = conn.cursor()

    # Create table if not exists
    c.execute('''
        CREATE TABLE IF NOT EXISTS stock_prices (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            stock      TEXT    NOT NULL,
            price      REAL    NOT NULL,
            prev_close REAL    NOT NULL,
            change     REAL    NOT NULL,
            change_pct REAL    NOT NULL,
            date       TEXT    NOT NULL,
            time       TEXT    NOT NULL
        )
    ''')

    conn.commit()
    conn.close()
    print("  Database initialized!")

# ── Save prices to database ───────────────────────────────
def save_prices(data):
    conn = sqlite3.connect(DB_FILE)
    c    = conn.cursor()

    now  = datetime.now(IST)
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    for stock, d in data.items():
        # Skip metadata keys
        if stock.startswith("_"):
            continue

        c.execute('''
            INSERT INTO stock_prices
            (stock, price, prev_close, change, change_pct, date, time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            stock,
            d.get("price",      0.0),
            d.get("prev_close", 0.0),
            d.get("change",     0.0),
            d.get("change_pct", 0.0),
            date,
            time
        ))

    conn.commit()
    conn.close()

# ── Get today's high and low for a stock ─────────────────
def get_today_high_low(stock):
    conn = sqlite3.connect(DB_FILE)
    c    = conn.cursor()

    today = datetime.now(IST).strftime("%Y-%m-%d")

    c.execute('''
        SELECT MAX(price), MIN(price)
        FROM stock_prices
        WHERE stock = ? AND date = ?
    ''', (stock, today))

    row = c.fetchone()
    conn.close()

    if row and row[0] is not None:
        return row[0], row[1]   # high, low
    return 0.0, 0.0

# ── Get last N prices for a stock ─────────────────────────
def get_recent_prices(stock, limit=10):
    conn = sqlite3.connect(DB_FILE)
    c    = conn.cursor()

    c.execute('''
        SELECT price, time
        FROM stock_prices
        WHERE stock = ?
        ORDER BY id DESC
        LIMIT ?
    ''', (stock, limit))

    rows = c.fetchall()
    conn.close()
    return rows

# ── Get today's first price (opening) ────────────────────
def get_today_open(stock):
    conn = sqlite3.connect(DB_FILE)
    c    = conn.cursor()

    today = datetime.now(IST).strftime("%Y-%m-%d")

    c.execute('''
        SELECT price FROM stock_prices
        WHERE stock = ? AND date = ?
        ORDER BY id ASC
        LIMIT 1
    ''', (stock, today))

    row = c.fetchone()
    conn.close()

    return row[0] if row else 0.0

if __name__ == "__main__":
    init_db()
    print("Database ready!")

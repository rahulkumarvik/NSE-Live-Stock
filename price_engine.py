import yfinance as yf
import json
import time
import socket
import threading
from datetime import datetime
import pytz
from database import init_db, save_prices

# ── Config ────────────────────────────────────────────────
PRICES_FILE  = "/home/coconut/stockengine/tmp/prices.json"
IST          = pytz.timezone("Asia/Kolkata")
save_counter = 0

STOCKS = {
    "RELIANCE": "RELIANCE.NS",
    "TCS":      "TCS.NS",
    "INFY":     "INFY.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "WIPRO":    "WIPRO.NS"
}

# ── Internet check ────────────────────────────────────────
def is_connected():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def wait_for_internet():
    print("  Checking internet...")
    while not is_connected():
        print("  No internet. Retrying in 5 seconds...")
        time.sleep(5)
    print("  Internet connected!\n")

# ── Market hours ──────────────────────────────────────────
def is_market_open():
    now = datetime.now(IST)
    if now.weekday() >= 5:
        return False
    market_open  = now.replace(hour=9,  minute=15, second=0)
    market_close = now.replace(hour=15, minute=30, second=0)
    return market_open <= now <= market_close

def get_market_status():
    now = datetime.now(IST)
    if now.weekday() >= 5:
        return "Weekend - Market Closed"
    if now < now.replace(hour=9, minute=15, second=0):
        return "Market opens at 9:15 AM"
    if now > now.replace(hour=15, minute=30, second=0):
        return "Market Closed"
    return "Market Open"

# ── Fetch one stock ───────────────────────────────────────
def get_data(symbol):
    try:
        ticker     = yf.Ticker(symbol)
        info       = ticker.fast_info
        current    = round(float(info.last_price), 2)
        prev_close = round(float(info.previous_close), 2)
        change     = round(current - prev_close, 2)
        change_pct = round((change / prev_close) * 100, 2)
        return {
            "price":      current,
            "prev_close": prev_close,
            "change":     change,
            "change_pct": change_pct
        }
    except Exception as e:
        print(f"    Error {symbol}: {e}")
        return {
            "price":      0.0,
            "prev_close": 0.0,
            "change":     0.0,
            "change_pct": 0.0
        }

# ── Fetch all stocks simultaneously ──────────────────────
def fetch_one(name, symbol, result):
    result[name] = get_data(symbol)

def fetch_all():
    result  = {}
    threads = []

    for name, symbol in STOCKS.items():
        t = threading.Thread(target=fetch_one, args=(name, symbol, result))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    return result

# ── Main loop ─────────────────────────────────────────────
def main():
    global save_counter

    print("=" * 40)
    print("  NSE PRICE ENGINE STARTING")
    print("=" * 40)

    init_db()
    wait_for_internet()

    while True:
        if not is_connected():
            print("Internet lost! Waiting...")
            wait_for_internet()

        now    = datetime.now(IST).strftime("%H:%M:%S")
        result = fetch_all()

        # Build data
        data = {}
        for name in STOCKS:
            data[name] = result.get(name, {
                "price":      0.0,
                "prev_close": 0.0,
                "change":     0.0,
                "change_pct": 0.0
            })
            d     = data[name]
            arrow = "▲" if d["change"] >= 0 else "▼"
            print(f"  {name:10} ₹{d['price']:<10}  {arrow} {d['change_pct']:+.2f}%")

        # Add metadata
        data["_status"] = "open" if is_market_open() else "closed"
        data["_time"]   = now
        data["_market"] = get_market_status()

        # Save to JSON file
        with open(PRICES_FILE, "w") as f:
            json.dump(data, f, indent=2)

        print(f"  [{now}] Saved to prices.json")

        # Save to SQLite every 1 minute
        save_counter += 1
        if save_counter >= 12:
            save_prices(data)
            save_counter = 0
            print("  Saved to database!")

        print()
        time.sleep(5 if is_market_open() else 60)

if __name__ == "__main__":
    main()

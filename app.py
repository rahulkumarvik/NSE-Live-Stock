import tkinter as tk
import yfinance as yf
import json
import time
import socket
import threading
from datetime import datetime
import pytz
from database import init_db, save_prices, get_today_high_low

# ── Config ────────────────────────────────────────────────
PRICES_FILE = "/home/coconut/stockengine/tmp/prices.json"
CONFIG_FILE  = "/home/coconut/stockengine/data/config.json"
REFRESH_MS   = 3000
IST          = pytz.timezone("Asia/Kolkata")
save_counter = 0
shared_data  = {}
data_lock    = threading.Lock()

STOCKS = {
    "RELIANCE": "RELIANCE.NS",
    "TCS":      "TCS.NS",
    "INFY":     "INFY.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "WIPRO":    "WIPRO.NS"
}

# ── Initialize database ───────────────────────────────────
init_db()

# ── Internet check ────────────────────────────────────────
def is_connected():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def wait_for_internet():
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
        return {"price": 0.0, "prev_close": 0.0, "change": 0.0, "change_pct": 0.0}

# ── Fetch one stock in thread ─────────────────────────────
def fetch_one(name, symbol, result):
    result[name] = get_data(symbol)

# ── Price feed thread ─────────────────────────────────────
def price_feed():
    global shared_data, save_counter

    print("NSE Price Feed Starting...")
    wait_for_internet()

    while True:
        if not is_connected():
            print("Internet lost! Waiting...")
            wait_for_internet()

        now    = datetime.now(IST).strftime("%H:%M:%S")
        result = {}

        # Fetch all stocks simultaneously
        threads = []
        for name, symbol in STOCKS.items():
            t = threading.Thread(target=fetch_one, args=(name, symbol, result))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Build data
        new_data = {}
        for name in STOCKS:
            new_data[name] = result.get(name, {
                "price": 0.0, "prev_close": 0.0,
                "change": 0.0, "change_pct": 0.0
            })
            d     = new_data[name]
            arrow = "▲" if d["change"] >= 0 else "▼"
            print(f"  {name:10} ₹{d['price']}  {arrow} {d['change_pct']:+.2f}%")

        new_data["_status"] = "open" if is_market_open() else "closed"
        new_data["_time"]   = now
        new_data["_market"] = get_market_status()

        # Save to shared memory
        with data_lock:
            shared_data = new_data

        # Save to file
        with open(PRICES_FILE, "w") as f:
            json.dump(new_data, f, indent=2)

        print(f"  Saved! [{now}]")

        # Save to database every 1 minute (12 x 5 seconds)
        save_counter += 1
        if save_counter >= 12:
            save_prices(new_data)
            save_counter = 0
            print("  Saved to database!\n")

        time.sleep(5 if is_market_open() else 60)

# ── Load data from shared memory ──────────────────────────
def load_data():
    with data_lock:
        return dict(shared_data)

# ── Widget update ─────────────────────────────────────────
def update():
    data = load_data()

    for name, row_labels in stock_labels.items():
        if name in data:
            d = data[name]

            if isinstance(d, dict):
                price      = d.get("price",      0.0)
                change     = d.get("change",      0.0)
                change_pct = d.get("change_pct",  0.0)
            else:
                price      = float(d)
                change     = 0.0
                change_pct = 0.0

            color = "#00ff88" if change >= 0 else "#ff4444"
            arrow = "▲"      if change >= 0 else "▼"

            row_labels["price"].config(
                text=f"₹{price:.2f}",
                fg="#ffffff"
            )
            row_labels["change"].config(
                text=f"{arrow} {change_pct:+.2f}%",
                fg=color
            )

            # Show today high and low
            high, low = get_today_high_low(name)
            if high > 0:
                row_labels["highlow"].config(
                    text=f"H:{high:.0f} L:{low:.0f}",
                    fg="#888888"
                )

    # Update market status
    if "_status" in data:
        if data["_status"] == "open":
            status_label.config(
                text=f"  🟢 {data['_market']} | {data['_time']} IST  ",
                fg="#00ff88"
            )
        else:
            status_label.config(
                text=f"  🔴 {data['_market']}  ",
                fg="#ff4444"
            )

    root.after(REFRESH_MS, update)

# ── Position save/load ────────────────────────────────────
def save_position():
    config = {"x": root.winfo_x(), "y": root.winfo_y()}
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def load_position():
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            return config.get("x", 100), config.get("y", 100)
    except:
        return 100, 100

# ── Build window ──────────────────────────────────────────
root = tk.Tk()
root.title("NSE Live")
root.attributes("-topmost", True)
root.attributes("-alpha", 0.92)
root.resizable(False, False)
root.configure(bg="#1e1e1e")

def start_drag(event):
    root._drag_x = event.x
    root._drag_y = event.y

def do_drag(event):
    x = root.winfo_x() + event.x - root._drag_x
    y = root.winfo_y() + event.y - root._drag_y
    root.geometry(f"+{x}+{y}")
    save_position()

root.bind("<ButtonPress-1>", start_drag)
root.bind("<B1-Motion>", do_drag)

# Title
tk.Label(
    root,
    text="  📈 NSE LIVE  ",
    bg="#2d2d2d",
    fg="#00ff88",
    font=("Courier", 11, "bold"),
    pady=6
).pack(fill="x")

# Headers
header = tk.Frame(root, bg="#2d2d2d")
header.pack(fill="x", padx=10, pady=2)
tk.Label(header, text="STOCK",  bg="#2d2d2d", fg="#888888", font=("Courier", 8), width=10, anchor="w").pack(side="left")
tk.Label(header, text="PRICE",  bg="#2d2d2d", fg="#888888", font=("Courier", 8), width=10, anchor="e").pack(side="left")
tk.Label(header, text="CHANGE", bg="#2d2d2d", fg="#888888", font=("Courier", 8), width=12, anchor="e").pack(side="right")
tk.Label(header, text="H / L",  bg="#2d2d2d", fg="#888888", font=("Courier", 8), width=12, anchor="e").pack(side="right")

# Stock rows
stock_labels = {}
for stock in STOCKS.keys():
    row = tk.Frame(root, bg="#1e1e1e", pady=4)
    row.pack(fill="x", padx=10)

    tk.Label(
        row, text=stock,
        bg="#1e1e1e", fg="#ffffff",
        font=("Courier", 9, "bold"),
        width=10, anchor="w"
    ).pack(side="left")

    price_label = tk.Label(
        row, text="...",
        bg="#1e1e1e", fg="#ffffff",
        font=("Courier", 9),
        width=10, anchor="e"
    )
    price_label.pack(side="left")

    change_label = tk.Label(
        row, text="...",
        bg="#1e1e1e", fg="#00ccff",
        font=("Courier", 9, "bold"),
        width=12, anchor="e"
    )
    change_label.pack(side="right")

    highlow_label = tk.Label(
        row, text="",
        bg="#1e1e1e", fg="#888888",
        font=("Courier", 8),
        width=16, anchor="e"
    )
    highlow_label.pack(side="right")

    stock_labels[stock] = {
        "price":   price_label,
        "change":  change_label,
        "highlow": highlow_label
    }

# Divider
tk.Frame(root, bg="#333333", height=1).pack(fill="x", padx=5)

# Status bar
status_label = tk.Label(
    root,
    text="  Starting...  ",
    bg="#2d2d2d",
    fg="#555555",
    font=("Courier", 8),
    pady=3
)
status_label.pack(fill="x")

# ── Start background thread ───────────────────────────────
thread = threading.Thread(target=price_feed, daemon=True)
thread.start()

# ── Load saved position ───────────────────────────────────
x, y = load_position()
root.geometry(f"+{x}+{y}")

# ── Start widget ──────────────────────────────────────────
update()
root.mainloop()

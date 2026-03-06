import yfinance as yf
import json
import time
import socket

OUTPUT_FILE = "/home/coconut/stockengine/tmp/prices.json"

STOCKS = {
    "RELIANCE": "RELIANCE.NS",
    "TCS":      "TCS.NS",
    "INFY":     "INFY.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "WIPRO":    "WIPRO.NS"
}

# ── Check internet connection ─────────────────────────────
def is_connected():
    try:
        # Try connecting to Google DNS
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

# ── Wait until internet is available ─────────────────────
def wait_for_internet():
    print("Checking internet connection...")
    while not is_connected():
        print("  No internet. Retrying in 5 seconds...")
        time.sleep(5)
    print("  Internet connected!\n")

# ── Fetch stock data ──────────────────────────────────────
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
        print(f"    Error: {symbol}: {e}")
        return {
            "price":      0.0,
            "prev_close": 0.0,
            "change":     0.0,
            "change_pct": 0.0
        }

# ── Main ──────────────────────────────────────────────────
def main():
    print("=" * 40)
    print("  NSE PRICE FEED STARTING")
    print("=" * 40)

    # Wait for internet before doing anything
    wait_for_internet()

    while True:

        # Check internet before each fetch
        if not is_connected():
            print("Internet lost! Waiting...")
            wait_for_internet()

        data = {}
        print("Fetching prices...")

        for name, symbol in STOCKS.items():
            d = get_data(symbol)
            data[name] = d
            arrow = "▲" if d["change"] >= 0 else "▼"
            print(f"  {name:10} ₹{d['price']}  {arrow} {d['change_pct']:+.2f}%")

        with open(OUTPUT_FILE, "w") as f:
            json.dump(data, f, indent=2)

        print("  Saved! Waiting 5 seconds...\n")
        time.sleep(5)

if __name__ == "__main__":
    main()

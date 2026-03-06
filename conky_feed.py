import json

PRICES_FILE = "/home/coconut/stockengine/tmp/prices.json"

# Conky color codes
GREEN = "${color1}"
RED   = "${color2}"
WHITE = "${color}"
GRAY  = "${color3}"

STOCKS = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "WIPRO"]

def load_data():
    try:
        with open(PRICES_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def main():
    data = load_data()

    if not data:
        print(f"{RED}Waiting for price feed...{WHITE}")
        return

    for stock in STOCKS:
        if stock not in data:
            continue

        d = data[stock]

        if isinstance(d, dict):
            price      = d.get("price",      0.0)
            change     = d.get("change",      0.0)
            change_pct = d.get("change_pct",  0.0)
        else:
            price      = float(d)
            change     = 0.0
            change_pct = 0.0

        color = GREEN if change >= 0 else RED
        arrow = "▲"   if change >= 0 else "▼"

        print(f"{WHITE}{stock:<10}{color}₹{price:<10.2f}{arrow} {change_pct:+.2f}%{WHITE}")

    # Market status
    if "_status" in data:
        print("")
        if data["_status"] == "open":
            print(f"{GREEN}🟢 {data.get('_market', 'Market Open')}{WHITE}")
        else:
            print(f"{RED}🔴 {data.get('_market', 'Market Closed')}{WHITE}")

if __name__ == "__main__":
    main()

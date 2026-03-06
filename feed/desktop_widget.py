import tkinter as tk
import json

PRICES_FILE = "/home/coconut/stockengine/tmp/prices.json"
REFRESH_MS  = 3000

def load_data():
    try:
        with open(PRICES_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def update():
    data = load_data()

    for name, row_labels in stock_labels.items():
        if name in data:
            d = data[name]

            # ── Handle both old and new format safely ──
            # Old format: {"RELIANCE": 1416.3}
            # New format: {"RELIANCE": {"price": 1416.3, ...}}
            if isinstance(d, dict):
                # New format
                price      = d.get("price",      0.0)
                change     = d.get("change",      0.0)
                change_pct = d.get("change_pct",  0.0)
            else:
                # Old format — just a number
                price      = float(d)
                change     = 0.0
                change_pct = 0.0

            if change >= 0:
                color = "#00ff88"
                arrow = "▲"
            else:
                color = "#ff4444"
                arrow = "▼"

            row_labels["price"].config(
                text=f"₹{price:.2f}",
                fg="#ffffff"
            )
            row_labels["change"].config(
                text=f"{arrow} {change_pct:+.2f}%",
                fg=color
            )

    # Update market status
    if "_status" in data:
        if data["_status"] == "open":
            status_label.config(
                text=f"  Market Open | {data['_time']} IST  ",
                fg="#00ff88"
            )
        else:
            status_label.config(
                text=f"  Market Closed | {data['_time']} IST  ",
                fg="#ff4444"
            )

    root.after(REFRESH_MS, update)

# ── Window ────────────────────────────────────────────────
root = tk.Tk()
root.title("NSE Live")
root.attributes("-topmost", True)
root.attributes("-alpha", 0.92)
root.resizable(False, False)
root.configure(bg="#1e1e1e")

# Draggable
def start_drag(event):
    root._drag_x = event.x
    root._drag_y = event.y

def do_drag(event):
    x = root.winfo_x() + event.x - root._drag_x
    y = root.winfo_y() + event.y - root._drag_y
    root.geometry(f"+{x}+{y}")

root.bind("<ButtonPress-1>", start_drag)
root.bind("<B1-Motion>", do_drag)

# Title
tk.Label(
    root,
    text="  NSE LIVE  ",
    bg="#2d2d2d",
    fg="#00ff88",
    font=("Courier", 11, "bold"),
    pady=6
).pack(fill="x")

# Column headers
header = tk.Frame(root, bg="#2d2d2d")
header.pack(fill="x", padx=10, pady=2)
tk.Label(header, text="STOCK",  bg="#2d2d2d", fg="#888888", font=("Courier", 8), width=10, anchor="w").pack(side="left")
tk.Label(header, text="PRICE",  bg="#2d2d2d", fg="#888888", font=("Courier", 8), width=10, anchor="e").pack(side="left")
tk.Label(header, text="CHANGE", bg="#2d2d2d", fg="#888888", font=("Courier", 8), width=12, anchor="e").pack(side="right")

# Stock rows
STOCKS = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "WIPRO"]
stock_labels = {}

for stock in STOCKS:
    row = tk.Frame(root, bg="#1e1e1e", pady=4)
    row.pack(fill="x", padx=10)

    tk.Label(
        row,
        text=stock,
        bg="#1e1e1e",
        fg="#ffffff",
        font=("Courier", 9, "bold"),
        width=10,
        anchor="w"
    ).pack(side="left")

    price_label = tk.Label(
        row,
        text="...",
        bg="#1e1e1e",
        fg="#ffffff",
        font=("Courier", 9),
        width=10,
        anchor="e"
    )
    price_label.pack(side="left")

    change_label = tk.Label(
        row,
        text="...",
        bg="#1e1e1e",
        fg="#00ccff",
        font=("Courier", 9, "bold"),
        width=12,
        anchor="e"
    )
    change_label.pack(side="right")

    stock_labels[stock] = {
        "price":  price_label,
        "change": change_label
    }

# Divider
tk.Frame(root, bg="#333333", height=1).pack(fill="x", padx=5)

# Market status
status_label = tk.Label(
    root,
    text="  checking market...  ",
    bg="#2d2d2d",
    fg="#555555",
    font=("Courier", 8),
    pady=3
)
status_label.pack(fill="x")

update()
root.mainloop()

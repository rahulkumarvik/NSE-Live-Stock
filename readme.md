# NSE Live Desktop Stocks

A live NSE stock price tracker for Ubuntu desktop.

## What it does
- Fetches live NSE stock prices every 5 seconds
- Shows price change from yesterday's close (green = up, red = down)
- Shows today's high and low prices
- Detects market hours (9:15 AM - 3:30 PM IST)
- Waits for internet before starting
- Saves price history to SQLite every 1 minute
- Auto starts when Ubuntu boots

## Two Display Modes

### 1. Tkinter Desktop Widget (app.py)
- Small floating dark window
- Always on top
- Draggable — remembers position
- Shows price, change %, high/low

### 2. Conky Desktop Overlay (conky_feed.py)
- Renders directly on desktop wallpaper
- No window, no titlebar
- Semi-transparent background

## Tech Stack
- Python 3
- C++ (price display)
- yfinance (market data)
- SQLite (price history)
- tkinter (desktop widget)
- Conky (desktop overlay)

## Stocks Tracked
- RELIANCE
- TCS
- INFY
- HDFCBANK
- WIPRO

## Setup
```bash
pip3 install yfinanc![Uploading 8b417e50-4f73-446f-abc3-3dcf2ac9288d.jpeg…]()
e pytz
sudo apt install conky-all python3-tk
```

### Run tkinter widget
```bash
python3 app.py
```

### Run Conky overlay
```bash
python3 price_engine.py
conky -c ~/.config/conky/nse.conf
```

## Project Structure
```
stockengine/
├── app.py            → tkinter widget + price feed
├── price_engine.py   → price feed + SQLite (for Conky)
├── database.py       → SQLite functions
├── conky_feed.py     → formats prices for Conky
├── src/
│   └── main.cpp      → C++ price display
├── start.sh          → auto startup script
└── README.md
```



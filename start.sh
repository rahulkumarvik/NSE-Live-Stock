#!/bin/bash
export DISPLAY=:0

# Wait for internet
sleep 15

# Start price engine (fetches + saves)
python3 /home/coconut/stockengine/price_engine.py &

# Wait for first fetch
sleep 8

# Start Conky display
conky -c /home/coconut/.config/conky/nse.conf &

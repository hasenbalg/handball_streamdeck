StreamDeck Scoreboard Controller

A lightweight Python-based controller that connects an Elgato Stream Deck to your custom scoreboard application via Socket.IO.
This tool lets you trigger scoreboard actions (score changes, timer control, etc.) directly from physical buttons — perfect for sports production, livestream overlays, or arena control.

## dev setup
python -m venv env
source env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt



## build
pyinstaller --onefile main.py
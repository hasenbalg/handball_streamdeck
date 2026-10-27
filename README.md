# StreamDeck Scoreboard Controller

A lightweight Python-based controller that connects an Elgato Stream Deck to [handball_scorebug](https://github.com/hasenbalg/handball_scorebug) via Socket.IO.
This tool lets you trigger scoreboard actions (score changes, timer control, etc.) directly from physical buttons — perfect for sports production, livestream overlays, or arena control.

<video controls src="video.mp4" title="Title"></video>

## Button layout (15 keys)

| Key | Action | Key | Action |
|---|---|---|---|
| 0 | Home +1 | 8 | Technical timeout |
| 1 | Away +1 | 9 | Next period |
| 2 | Timer start (dot when clock is stopped) | 10 | Home −1 (undo goal) |
| 3 | Timer stop (dot when running) | 11 | Away −1 (undo goal) |
| 4 | Home timeout | 12 | Passive home signal (dot when armed) |
| 5 | Away timeout | 13 | Passive away signal (dot when armed) |
| 6 | Side change | 14 | Passive pass −1 |
| 7 | Referee whistle (dot when running) | | |

Keys 0–6 keep the original positions. Team border colors and the
state dots follow the live scorebug state; key images are only
re-uploaded when they actually change. `skip_break` and
`log_delete_last` are intentionally not on the deck (15 keys full).

Note: goal buttons send `home/away_score_change`; these payloads only
started entering the scorebug's match log after
[handball_scorebug#28](https://github.com/hasenbalg/handball_scorebug/pull/28).

## dev setup
```
python -m venv env
source env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## tests
```
python -m unittest discover -s tests
```

## build
```
pyinstaller --onefile main.py
```

## install & run
```
wget https://github.com/hasenbalg/handball_streamdeck/releases/download/init/handball_streamdeck
./handball_streamdeck
```

Point it at the scorebug with `--host`/`--port` (defaults
`localhost:80`); the client retries the initial connection and
reconnects on drops, so the scoreboard container may start later.

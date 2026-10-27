"""Elgato Stream Deck controller for handball_scorebug.

Connects to the scorebug's Socket.IO server, triggers actions from
physical buttons and paints live state (team colors, running/paused
dot, passive-armed dots) onto the keys.

Key layout (keys 0-6 keep their historical positions):

    0 Home +1   1 Away +1   2 Timer Start  3 Timer Stop
    4 TO Home   5 TO Away   6 Side Change
    7 Whistle   8 Tech TO   9 Next Period
   10 Home -1  11 Away -1  12 Passive Home  13 Passive Away  14 Pass -1

Status dots: Timer Start (clock stopped), Timer Stop / Whistle (clock
running), Passive Home/Away (signal armed), Pass -1 (any passive on).
"""

import argparse
import time

# ---------------------------------------------------------------------
# Button layout — pure data, importable without a Stream Deck attached
# ---------------------------------------------------------------------
# press: payload emitted on the "update" event, None = no action
# color: "home"/"away" pulls the border color from state
# dot:   predicate over the state dict -> white status dot

BUTTONS = [
    {"label": "Home +1",        "press": {"home_score_change": 1},  "color": "home"},
    {"label": "Away +1",        "press": {"away_score_change": 1},  "color": "away"},
    {"label": "Timer\nStart",   "press": {"start_timer": True},     "dot": lambda s: not s.get("running")},
    {"label": "Timer\nStop",    "press": {"stop_timer": True},      "dot": lambda s: bool(s.get("running"))},
    {"label": "Home\nTimeout",  "press": {"timeout_home": True},    "color": "home"},
    {"label": "Away\nTimeout",  "press": {"timeout_away": True},    "color": "away"},
    {"label": "Side\nChange",   "press": {"side_change": True}},
    {"label": "Whistle\n(2:8)", "press": {"referee_whistle": True}, "dot": lambda s: bool(s.get("running"))},
    {"label": "Technical\nTimeout", "press": {"technical_timeout": True}},
    {"label": "Next\nPeriod",   "press": {"next_period": True}},
    {"label": "Home −1\nundo",  "press": {"home_score_change": -1}, "color": "home"},
    {"label": "Away −1\nundo",  "press": {"away_score_change": -1}, "color": "away"},
    {"label": "Passive\nHome",  "press": {"passive_home": True},    "color": "home",
     "dot": lambda s: s.get("passive_team") == "home"},
    {"label": "Passive\nAway",  "press": {"passive_away": True},    "color": "away",
     "dot": lambda s: s.get("passive_team") == "away"},
    {"label": "Pass\n−1",       "press": {"passive_pass": True},
     "dot": lambda s: s.get("passive_team") is not None},
]


def key_visuals(state, index):
    """(label, color, dot) for one key — doubles as its render
    signature so unchanged keys are not re-uploaded over USB (#2)."""
    btn = BUTTONS[index]
    color = None
    if btn.get("color") == "home":
        color = state.get("home_color")
    elif btn.get("color") == "away":
        color = state.get("away_color")
    dot = bool(btn["dot"](state)) if "dot" in btn else False
    return btn["label"], color, dot


def press_payload(index):
    return BUTTONS[index]["press"]

# ---------------------------------------------------------------------
# Entry point — everything hardware/IO lives here
# ---------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description=(__doc__ or "handball_streamdeck").splitlines()[0])
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", default="80")
    args = parser.parse_args()

    url = f"http://{args.host}:{args.port}"

    from StreamDeck.DeviceManager import DeviceManager
    from StreamDeck.ImageHelpers import PILHelper
    from PIL import Image, ImageDraw, ImageFont
    import socketio

    # -- socket connection with retry (#3) -----------------------------
    sio = socketio.Client(reconnection=True, reconnect_max_delay=5)

    def connect():
        attempt = 0
        while not sio.connected:
            try:
                sio.connect(url, wait_timeout=10)
                print(f"connected to {url} (use --host/--port to change)")
            except Exception as e:
                attempt += 1
                print(f"connect failed ({e}); retry in 3 s (attempt {attempt})")
                time.sleep(3)

    # -- stream deck ----------------------------------------------------
    decks = DeviceManager().enumerate()
    if not decks:
        raise SystemExit("no Stream Deck found")
    deck = decks[0]
    deck.open()
    deck.reset()

    def load_font():
        for name in ("DejaVuSans.ttf",
                     "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                     "arial.ttf"):
            try:
                return ImageFont.truetype(name, 18)
            except OSError:
                continue
        return ImageFont.load_default()

    font = load_font()

    def render_key_image(label, color=None, render_dot=False):
        image = PILHelper.create_image(deck)
        draw = ImageDraw.Draw(image)
        bbox = draw.textbbox((0, 0), label, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (image.width - w) // 2
        y = (image.height - h) // 2
        draw.text((x, y), label, font=font, fill="white")
        if color:
            draw.rounded_rectangle((0, 0, image.width - 6, image.height - 6),
                                   outline=color, width=3, radius=10)
        if render_dot:
            r = 6
            cx, cy = image.width // 2, int(image.height * 0.85)
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill="white")
        return PILHelper.to_native_format(deck, image)

    # -- render on change only (#2) --------------------------------------
    shown = {}

    def refresh(state):
        state = state or {}
        for i in range(len(BUTTONS)):
            sig = key_visuals(state, i)
            if shown.get(i) != sig:
                deck.set_key_image(i, render_key_image(*sig))
                shown[i] = sig

    def key_change(_deck, key, pressed):
        if not pressed:  # key released
            return
        payload = press_payload(key)
        if payload is None:
            return
        try:
            print(f"sending {payload}")
            sio.emit("update", payload)
        except Exception as e:
            print(f"emit failed ({e}); reconnecting")
            connect()

    deck.set_key_callback(key_change)

    @sio.on("state_update")
    def on_state(data=None):
        refresh(data)

    @sio.on("connect")
    def on_connect():
        refresh({})  # repaint once the link is back

    connect()
    refresh({})

    # Keep the script alive (prevents libusb crash)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        deck.reset()
        deck.close()


if __name__ == "__main__":
    main()

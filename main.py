from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper
from PIL import Image, ImageDraw, ImageFont
import socketio
import time
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--host", default="localhost")
parser.add_argument("--port", default="80")
args = parser.parse_args()

url = f"http://{args.host}:{args.port}"


# ---------------------------------------------------------
# Socket.IO connection
# ---------------------------------------------------------
sio = socketio.Client()
sio.connect(url)
print(f"connected to {url}. use --host and --port for change")

def send_update(payload):
    print(f"sending {payload}")
    sio.emit("update", payload)

# ---------------------------------------------------------
# Stream Deck setup
# ---------------------------------------------------------
deck = DeviceManager().enumerate()[0]
deck.open()
deck.reset()

# ---------------------------------------------------------
# Render text onto a Stream Deck button
# ---------------------------------------------------------
def render_key_image(deck, text):
    # Create a correctly sized blank image for this deck model
    image = PILHelper.create_image(deck)
    draw = ImageDraw.Draw(image)

    # Load a font
    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except:
        font = ImageFont.load_default()

    # Measure text
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]

    # Center text
    x = (image.width - w) // 2
    y = (image.height - h) // 2

    draw.text((x, y), text, font=font, fill="white")

    # Convert to native Stream Deck format
    return PILHelper.to_native_format(deck, image)

# ---------------------------------------------------------
# Button press handler
# ---------------------------------------------------------
def key_change(deck, key, state):
    if state:  # key pressed
        if key == 0:
            send_update({"home_score_change": 1})
        elif key == 1:
            send_update({"away_score_change": 1})
        elif key == 2:
            send_update({"start_timer": True})
        elif key == 3:
            send_update({"stop_timer": True})
        elif key == 4:
            send_update({"timeout_home": True})
        elif key == 5:
            send_update({"timeout_away": True})

deck.set_key_callback(key_change)

# ---------------------------------------------------------
# Set button labels
# ---------------------------------------------------------
deck.set_key_image(0, render_key_image(deck, "Home +1"))
deck.set_key_image(1, render_key_image(deck, "Away +1"))
deck.set_key_image(2, render_key_image(deck, "Timer\nStart"))
deck.set_key_image(3, render_key_image(deck, "Timer\nStop"))

deck.set_key_image(4, render_key_image(deck, "Home\nTimeout"))
deck.set_key_image(5, render_key_image(deck, "Away\nTimeout"))

# ---------------------------------------------------------
# Keep script alive (prevents libusb crash)
# ---------------------------------------------------------
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    deck.reset()
    deck.close()

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
def render_key_image(deck, text, color=None, render_dot=False):
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
    if color:
        draw.rounded_rectangle((0, 0, image.width - 6, image.height - 6), outline=color, width=3, radius=10)
    if render_dot:
        draw.ellipse([(image.width/2, image.height * .8), ((image.width/2)+2, (image.height * .8)+2)], width=10, fill="white")

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
        elif key == 6:
            send_update({"side_change": True})

deck.set_key_callback(key_change)

# ---------------------------------------------------------
# Set button labels
# ---------------------------------------------------------
@sio.on('state_update')
def render_key_images(data=None):
    home_color = data['home_color'] if data else None
    away_color = data['away_color'] if data else None
    running = data["running"] if data else None
    deck.set_key_image(0, render_key_image(deck, "Home +1", home_color))
    deck.set_key_image(1, render_key_image(deck, "Away +1", away_color))
    deck.set_key_image(2, render_key_image(deck, "Timer\nStart", None, not running))
    deck.set_key_image(3, render_key_image(deck, "Timer\nStop", None, running))

    deck.set_key_image(4, render_key_image(deck, "Home\nTimeout", home_color))
    deck.set_key_image(5, render_key_image(deck, "Away\nTimeout", away_color))
    deck.set_key_image(6, render_key_image(deck, "Side\nChange"))

# ---------------------------------------------------------
# Keep script alive (prevents libusb crash)
# ---------------------------------------------------------
render_key_images(None)
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    deck.reset()
    deck.close()

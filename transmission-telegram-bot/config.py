import os
import json

from dotenv import load_dotenv

load_dotenv()

allowed_updaters = ["ngrok", "webserver", "polling"]

TOKEN = os.environ["TELEGRAM_TOKEN"]
PORT_NGROK_TUNNEL = 5000
WEBHOOK_PORT = 8080
WEBHOOK_DOMAIN = os.getenv("WEBHOOK_DOMAIN")
UPDATER_TYPE = os.getenv("UPDATER_TYPE", "polling")
if UPDATER_TYPE not in allowed_updaters:
    raise TypeError(
        f"No such updater.\n Available options: {', '.join(allowed_updaters)}"
    )

TRANSSMISION_HOST = os.getenv("TRANSSMISION_HOST", "127.0.0.1")
TRANSSMISION_PORT = int(os.getenv("TRANSSMISION_PORT", 9091))
TRANSSMISION_USERNAME = os.getenv("TRANSSMISION_USERNAME")
TRANSSMISION_PASSWORD = os.getenv("TRANSSMISION_PASSWORD")


_transmission_clients = os.getenv("TRANSMISSION_CLIENTS")
if _transmission_clients:
    TRANSMISSION_CLIENTS = json.loads(_transmission_clients)
else:
    TRANSMISSION_CLIENTS = [
        {
            "name": "Default",
            "host": TRANSSMISION_HOST,
            "port": TRANSSMISION_PORT,
            "username": TRANSSMISION_USERNAME,
            "password": TRANSSMISION_PASSWORD,
        }
    ]


_whitelist = os.environ["WHITELIST"]
WHITELIST = [int(i.strip()) for i in _whitelist.split(",")]

PROGRESS_BAR_EMOJIS = {"done": "📦", "inprogress": "⬜"}

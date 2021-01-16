import os
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

TRANSSMISION_HOST = os.environ["TRANSSMISION_HOST"]
TRANSSMISION_PORT = int(os.getenv("TRANSSMISION_PORT") or 9091)
TRANSSMISION_USERNAME = os.getenv("TRANSSMISION_USERNAME")
TRANSSMISION_PASSWORD = os.getenv("TRANSSMISION_PASSWORD")

_whitelist = os.environ["WHITELIST"]
WHITELIST = [int(i.strip()) for i in _whitelist.split(",")]

PROGRESS_BAR_EMOJIS = {"done": "📦", "inprogress": "⬜"}

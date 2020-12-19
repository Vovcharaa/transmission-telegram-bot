import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT_NGROK_TUNNEL = 5000

TRANSSMISION_HOST = os.getenv("TRANSSMISION_HOST")
TRANSSMISION_PORT = os.getenv("TRANSSMISION_PORT")
TRANSSMISION_USERNAME = os.getenv("TRANSSMISION_USERNAME")
TRANSSMISION_PASSWORD = os.getenv("TRANSSMISION_PASSWORD")


PROGRESS_BAR_EMOJIS = {"done": "📦", "inprogress": "⬜"}

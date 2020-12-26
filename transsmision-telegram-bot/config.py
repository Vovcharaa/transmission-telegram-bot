import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ["TELEGRAM_TOKEN"]
PORT_NGROK_TUNNEL = 5000

TRANSSMISION_HOST = os.environ["TRANSSMISION_HOST"]
TRANSSMISION_PORT = int(os.getenv("TRANSSMISION_PORT") or 9091)
TRANSSMISION_USERNAME = os.getenv("TRANSSMISION_USERNAME")
TRANSSMISION_PASSWORD = os.getenv("TRANSSMISION_PASSWORD")

_list_of_users = os.environ["LIST_OF_USERS"]
LIST_OF_USERS = [int(i.strip()) for i in _list_of_users.split(",")]

PROGRESS_BAR_EMOJIS = {"done": "📦", "inprogress": "⬜"}

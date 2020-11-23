import math
import time

import pyngrok.ngrok

from . import config


def setup_ngrok_webhook(updater):
    """
    Setups ngrok tunnel and telegram webhook on it
    """
    webhook_tunnel = pyngrok.ngrok.connect(
        addr=config.PORT, proto="http", options={"bind_tls": True}
    )
    time.sleep(1)
    public_url = webhook_tunnel.public_url
    webhook = public_url.replace("http:", "https:")
    updater.bot.set_webhook(f"{webhook}/{config.TOKEN}")
    updater.start_webhook(listen="127.0.0.1", port=config.PORT, url_path=config.TOKEN)


def progress_bar(percent: float):
    progres = math.floor(percent / 10)
    progres_string = (
        f'{config.PROGRESS_BAR_EMOJIS["done"] * progres}'
        f'{config.PROGRESS_BAR_EMOJIS["inprogress"] * (10-progres)}'
    )
    return progres_string

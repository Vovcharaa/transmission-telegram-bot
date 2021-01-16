import math
import time
import logging
from functools import wraps

import pyngrok.ngrok
import transmission_rpc as trans
from telegram.ext import Updater

from . import config

logger = logging.getLogger(__name__)


def setup_updater(updater: Updater):
    updaters = {
        "ngrok": setup_ngrok_webhook,
        "webserver": setup_webserver,
        "polling": setup_polling
    }
    updaters[config.UPDATER_TYPE](updater)


def setup_ngrok_webhook(updater: Updater):
    """
    Setups ngrok tunnel and set telegram webhook on it
    """
    logger.info("Setting ngrok webhook")
    logger.debug("Installing ngrok")
    pyngrok.ngrok.install_ngrok()
    logger.debug("Setuping tunnel")
    webhook_tunnel = pyngrok.ngrok.connect(
        addr=config.PORT_NGROK_TUNNEL, proto="http", options={"bind_tls": True}
    )
    time.sleep(1)
    public_url = webhook_tunnel.public_url
    webhook = public_url.replace("http:", "https:")
    logger.debug("Starting webhook")
    updater.start_webhook(
        listen="127.0.0.1", port=config.PORT_NGROK_TUNNEL, url_path=config.TOKEN
    )
    logger.debug("Setting webhook")
    updater.bot.set_webhook(f"{webhook}/{config.TOKEN}")


def setup_webserver(updater: Updater):
    """
    Setups webserver and set telegram webhook on it
    Provide WEBHOOK_DOMAIN for this type of receiving updates
    """
    if config.WEBHOOK_DOMAIN:
        logger.info("Starting webserver for webhook")
        updater.start_webhook(
            listen="0.0.0.0", port=config.WEBHOOK_PORT, url_path=config.TOKEN
        )
        logger.debug("Setting webhook")
        updater.bot.set_webhook(f"{config.WEBHOOK_DOMAIN}/{config.TOKEN}")
    else:
        raise TypeError("WEBHOOK_DOMAIN env variable is not provided")


def setup_polling(updater: Updater):
    """
    Polling type of receiving updates
    """
    updater.start_polling()


def progress_bar(percent: float) -> str:
    progres = math.floor(percent / 10)
    progres_string = (
        f'{config.PROGRESS_BAR_EMOJIS["done"] * progres}'
        f'{config.PROGRESS_BAR_EMOJIS["inprogress"] * (10-progres)}'
    )
    return progres_string


def formated_eta(torrent: trans.Torrent) -> str:
    try:
        eta = torrent.eta
    except ValueError:
        return "Unavailable"
    minutes, seconds = divmod(eta.seconds, 60)
    hours, minutes = divmod(minutes, 60)
    text = ""
    if eta.days:
        text += f"{eta.days} days "
    if hours:
        text += f"{hours} h {minutes} min"
    else:
        text += f"{minutes} min {seconds} sec"
    return text


def file_progress(file: trans.File) -> float:
    try:
        size = file.size
        completed = file.completed
        return 100.0 * (completed / size)
    except ZeroDivisionError:
        return 0.0


def whitelist(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in config.WHITELIST:
            logger.warning(f"Unauthorized access denied for {user_id}.")
            return
        return func(update, context, *args, **kwargs)
    return wrapped

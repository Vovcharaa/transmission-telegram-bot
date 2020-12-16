import time
import logging

import telegram
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, Updater
from telegram.ext.filters import Filters

from . import config, menus, utils


def start(update, context):
    text = menus.menu()
    update.message.reply_text(text, reply_markup=telegram.ReplyKeyboardRemove())


def add(update, context):
    text = menus.add_torrent()
    update.message.reply_text(text)


def memory(update, context):
    formatted_memory = menus.get_memory()
    update.message.reply_text(formatted_memory)


def get_torrents_command(update, context):
    torrent_list, keyboard = menus.get_torrents()
    update.message.reply_text(torrent_list, reply_markup=keyboard)


def get_torrents_inline(update, context):
    query = update.callback_query
    callback = query.data.split("_")
    start_point = int(callback[1])
    torrent_list, keyboard = menus.get_torrents(start_point)
    if len(callback) == 3 and callback[2] == "reload":
        try:
            query.edit_message_text(text=torrent_list, reply_markup=keyboard)
            query.answer(text="Reloaded")
        except telegram.error.BadRequest:
            query.answer(text="Nothing to reload")
    else:
        query.answer()
        query.edit_message_text(text=torrent_list, reply_markup=keyboard)


def torrent_menu_inline(update, context):
    query = update.callback_query
    callback = query.data.split("_")
    torrent_id = int(callback[1])
    if len(callback) == 3 and callback[2] != "reload":
        if callback[2] == "start":
            menus.start_torrent(torrent_id)
            query.answer(text="Started")
            time.sleep(0.2)
        elif callback[2] == "stop":
            menus.stop_torrent(torrent_id)
            query.answer(text="Stopped")
            time.sleep(0.2)
    text, reply_markup = menus.torrent_menu(torrent_id)
    if len(callback) == 3 and callback[2] == "reload":
        try:
            query.edit_message_text(text=text, reply_markup=reply_markup)
            query.answer(text="Reloaded")
        except telegram.error.BadRequest:
            query.answer(text="Nothing to reload")
    else:
        query.answer()
        query.edit_message_text(text=text, reply_markup=reply_markup)


def torrent_files_inline(update, context):
    query = update.callback_query
    callback = query.data.split("_")
    torrent_id = int(callback[1])
    text, reply_markup = menus.get_files(torrent_id)
    if len(callback) == 3 and callback[2] == "reload":
        try:
            query.edit_message_text(text=text, reply_markup=reply_markup)
            query.answer(text="Reloaded")
        except telegram.error.BadRequest:
            query.answer(text="Nothing to reload")
    else:
        query.answer()
        query.edit_message_text(text=text, reply_markup=reply_markup)


def delete_torrent_inline(update, context):
    query = update.callback_query
    callback = query.data.split("_")
    torrent_id = int(callback[1])
    text, reply_markup = menus.delete_menu(torrent_id)
    query.answer()
    query.edit_message_text(text=text, reply_markup=reply_markup)


def delete_torrent_action_inline(update, context):
    query = update.callback_query
    callback = query.data.split("_")
    torrent_id = int(callback[1])
    if len(callback) == 3 and callback[2] == "data":
        menus.delete_torrent(torrent_id, True)
    else:
        menus.delete_torrent(torrent_id)
    query.answer(text="✅Deleted")
    time.sleep(0.1)
    torrent_list, keyboard = menus.get_torrents()
    query.edit_message_text(text=torrent_list, reply_markup=keyboard)


def torrent_file_handler(update, context):
    file_bytes = context.bot.get_file(update.message.document).download_as_bytearray()
    torrent = menus.add_torrent_with_file(file_bytes)
    update.message.reply_text("Torrent added", quote=True)
    text, reply_markup = menus.add_menu(torrent.id)
    update.message.reply_text(text=text, reply_markup=reply_markup)


def magnet_url_handler(update, context):
    magnet_url = update.message.text
    torrent = menus.add_torrent_with_magnet(magnet_url)
    update.message.reply_text("Torrent added", quote=True)
    text, reply_markup = menus.add_menu(torrent.id)
    update.message.reply_text(text=text, reply_markup=reply_markup)


def after_adding(update, context):
    query = update.callback_query
    callback = query.data.split("_")
    torrent_id = int(callback[1])
    if len(callback) == 3 and callback[2] == "start":
        menus.start_torrent(torrent_id)
        query.answer(text="✅Started")
        text, reply_markup = menus.started_menu(torrent_id)
        query.edit_message_text(text=text, reply_markup=reply_markup)
    elif len(callback) == 3 and callback[2] == "cancel":
        menus.delete_torrent(torrent_id, True)
        query.answer(text="✅Canceled")
        query.edit_message_text("Torrent deleted🗑")


def run():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    bot = telegram.Bot(token=config.TOKEN)
    updater = Updater(token=config.TOKEN)
    utils.setup_ngrok_webhook(updater)
    updater.dispatcher.add_handler(
        MessageHandler(Filters.document.file_extension("torrent"), torrent_file_handler)
    )
    updater.dispatcher.add_handler(
        MessageHandler(Filters.regex(r"\Amagnet:\?xt=urn:btih:.*"), magnet_url_handler)
    )
    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CommandHandler("menu", start))
    updater.dispatcher.add_handler(CommandHandler("add", add))
    updater.dispatcher.add_handler(CommandHandler("memory", memory))
    updater.dispatcher.add_handler(CommandHandler("torrents", get_torrents_command))
    updater.dispatcher.add_handler(
        CallbackQueryHandler(after_adding, pattern="torrentadd_*")
    )
    updater.dispatcher.add_handler(
        CallbackQueryHandler(torrent_files_inline, pattern="torrentsfiles_*")
    )
    updater.dispatcher.add_handler(
        CallbackQueryHandler(delete_torrent_inline, pattern="deletemenutorrent_*")
    )
    updater.dispatcher.add_handler(
        CallbackQueryHandler(delete_torrent_action_inline, pattern="deletetorrent_*")
    )
    updater.dispatcher.add_handler(
        CallbackQueryHandler(get_torrents_inline, pattern="torrentsgoto_*")
    )
    updater.dispatcher.add_handler(
        CallbackQueryHandler(torrent_menu_inline, pattern="torrent_*")
    )
    bot = bot.get_me()
    logger.info("Started bot %s at https://t.me/%s", bot["first_name"], bot["username"])
    updater.idle()

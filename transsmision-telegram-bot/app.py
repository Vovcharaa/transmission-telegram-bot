import transmission_rpc as trans
import pyngrok.ngrok
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
import telegram
import time

TOKEN = "1333702154:AAHftoT9cd6HSjt8Zj16EfiVo2JQI1CtPRY"
PORT = 5000
transClient = trans.Client(host="192.168.0.200", port=9091)
DISK = "d:"

STATUS_LIST = {
    "downloading": "⏬",
    "seeding": "✅",
    "checking": "🔄",
    "check pending": "📡",
    "stopped": "🛑",
}


class TranssmissionTelegramBot:
    def setup_ngrok_webhook(updater):
        """
        Setups ngrok tunnel and telegram webhook on it
        """
        webhook_tunnel = pyngrok.ngrok.connect(
            addr=PORT, proto="http", options={"bind_tls": True}
        )
        time.sleep(1)
        public_url = webhook_tunnel.public_url
        webhook = public_url.replace("http:", "https:")
        updater.bot.set_webhook(f"{webhook}/{TOKEN}")
        updater.start_webhook(listen="127.0.0.1", port=PORT, url_path=TOKEN)

    def start(update, context):
        """
        start command
        """
        text = (
            "List of available commands:\n"
            "/torrents - List all torrents\n"
            "/memory - Available memory"
        )
        update.message.reply_text(text, reply_markup=telegram.ReplyKeyboardRemove())

    def memory(update, context):
        free_memory = trans.utils.format_size(transClient.free_space(DISK))
        formatted_memory = f"Вільно {round(free_memory[0], 2)} {free_memory[1]}"
        update.message.reply_text(formatted_memory)

    def get_torrents_command(update, context):
        torrent_list, keyboard = TranssmissionTelegramBot.get_torrents()
        update.message.reply_text(torrent_list, reply_markup=keyboard)

    def get_commands_inline(update, context):
        query = update.callback_query
        callback = query.data.split("_")
        start_point = int(callback[1])
        if len(callback) == 3 and callback[2] == "reload":
            torrent_list, keyboard = TranssmissionTelegramBot.get_torrents(start_point)
            try:
                query.edit_message_text(text=torrent_list, reply_markup=keyboard)
                query.answer(text="Reloaded")
            except telegram.error.BadRequest:
                query.answer(text="Nothing to reload")
        else:
            query.answer()
            torrent_list, keyboard = TranssmissionTelegramBot.get_torrents(start_point)
            query.edit_message_text(text=torrent_list, reply_markup=keyboard)

    def get_torrents(start_point=0):
        """
        Generates list of torrents with keyboard
        """
        SIZE_OF_LINE = 30
        KEYBORD_WIDTH = 5
        SIZE_OF_PAGE = 15
        torrents = transClient.get_torrents()
        torrents_count = 1
        count = start_point
        keyboard = [[]]
        column = 0
        row = 0
        torrent_list = ""
        for torrent in torrents[start_point:]:
            if torrents_count <= SIZE_OF_PAGE:
                if len(torrent.name) >= SIZE_OF_LINE:
                    name = (
                        f"{torrent.name[:SIZE_OF_LINE]}.."
                        f"   {STATUS_LIST[torrent.status]}"
                    )
                else:
                    name = torrent.name
                torrent_list += f"{count+1}. {name}\n"
                if column >= KEYBORD_WIDTH:
                    keyboard.append(list())
                    column = 0
                    row += 1
                keyboard[row].append(
                    telegram.InlineKeyboardButton(
                        f"{count+1}", callback_data=f"torrent_{count}"
                    )
                )
                column += 1
                count += 1
                torrents_count += 1
            else:
                keyboard.append(list())
                row += 1
                keyboard[row].append(
                    telegram.InlineKeyboardButton(
                        "🔄Reload",
                        callback_data=f"torrentsgoto_{start_point}_reload",
                    )
                )
                keyboard.append(list())
                row += 1
                if start_point != 0:
                    keyboard[row].append(
                        telegram.InlineKeyboardButton(
                            "⏪Back",
                            callback_data=f"torrentsgoto_{start_point - SIZE_OF_PAGE}",
                        )
                    )
                keyboard[row].append(
                    telegram.InlineKeyboardButton(
                        "Next⏩",
                        callback_data=f"torrentsgoto_{count}",
                    )
                )
                break
        else:
            keyboard.append(list())
            row += 1
            keyboard[row].append(
                telegram.InlineKeyboardButton(
                    "🔄Reload",
                    callback_data=f"torrentsgoto_{start_point}",
                )
            )
            keyboard.append(list())
            row += 1
            if start_point != 0:
                keyboard[row].append(
                    telegram.InlineKeyboardButton(
                        "⏪Back",
                        callback_data=f"torrentsgoto_{start_point - SIZE_OF_PAGE}",
                    )
                )

        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        return torrent_list, reply_markup

    def run():
        bot = telegram.Bot(token=TOKEN)
        updater = Updater(token=TOKEN)
        TranssmissionTelegramBot.setup_ngrok_webhook(updater)
        updater.dispatcher.add_handler(
            CommandHandler("start", TranssmissionTelegramBot.start)
        )
        updater.dispatcher.add_handler(
            CommandHandler("memory", TranssmissionTelegramBot.memory)
        )
        updater.dispatcher.add_handler(
            CommandHandler("torrents", TranssmissionTelegramBot.get_torrents_command)
        )
        updater.dispatcher.add_handler(
            CallbackQueryHandler(
                TranssmissionTelegramBot.get_commands_inline, pattern="torrentsgoto_*"
            )
        )
        print(bot.get_me())
        updater.idle()

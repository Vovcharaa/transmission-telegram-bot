import telegram
import transmission_rpc as trans
from . import config, utils
from typing import Tuple
import base64


STATUS_LIST = {
    "downloading": "⏬",
    "seeding": "✅",
    "checking": "🔄",
    "check pending": "📡",
    "stopped": "🛑",
}

transClient = trans.Client(
    host=config.TRANSSMISION_HOST,
    port=config.TRANSSMISION_PORT,
    username=config.TRANSSMISION_USERNAME,
    password=config.TRANSSMISION_PASSWORD,
)


def start_torrent(torrent_id: int):
    transClient.start_torrent(torrent_id)


def stop_torrent(torrent_id: int):
    transClient.stop_torrent(torrent_id)


def delete_torrent(torrent_id: int, data: bool = False):
    transClient.remove_torrent(torrent_id, delete_data=data)


def add_torrent_with_file(file):
    encoded_file = base64.b64encode(file).decode("utf-8")
    torrent = transClient.add_torrent(encoded_file, paused=True)
    return torrent


def add_torrent_with_magnet(url):
    torrent = transClient.add_torrent(url, paused=True)
    return torrent


def menu() -> str:
    text = (
        "List of available commands:\n"
        "/torrents - List all torrents\n"
        "/memory - Available memory\n"
        "/add - Add torrent"
    )
    return text


def add_torrent() -> str:
    text = "Just send torrent file or magnet url to the bot"
    return text


def get_memory() -> str:
    free_memory = trans.utils.format_size(transClient.free_space(config.DISK))
    formatted_memory = f"Free {round(free_memory[0], 2)} {free_memory[1]}"
    return formatted_memory


def torrent_menu(torrent_id: int) -> Tuple[str, telegram.InlineKeyboardMarkup]:
    torrent = transClient.get_torrent(torrent_id)
    text = (
        f"{torrent.name}\n"
        f"{utils.progress_bar(torrent.progress)}  {round(torrent.progress, 1)}% "
        f"{STATUS_LIST[torrent.status]}\n"
    )
    if download := torrent.rateDownload:
        speed = trans.utils.format_speed(download)
        text += (
            f"Time remaining: {utils.formated_eta(torrent)}\n"
            f"Download rate: {round(speed[0], 1)} {speed[1]}\n"
        )
    if torrent.status != "seeding":
        downloaded_bytes: int = torrent.sizeWhenDone - torrent.leftUntilDone
        downloaded = trans.utils.format_size(downloaded_bytes)
        text += f"Downloaded: {round(downloaded[0],2)} {downloaded[1]}\n"
    if upload := torrent.rateUpload:
        speed = trans.utils.format_speed(upload)
        text += f"Upload rate: {round(speed[0], 1)} {speed[1]}\n"
    sizeWhenDone = trans.utils.format_size(torrent.sizeWhenDone)
    total_size = trans.utils.format_size(torrent.totalSize)
    total_uploaded = trans.utils.format_size(torrent.uploadedEver)
    text += f"Total size for download: {round(sizeWhenDone[0], 2)} {sizeWhenDone[1]}\n"
    text += f"Total size: {round(total_size[0], 2)} {total_size[1]}\n"
    text += f"Total ever uploaded: {round(total_uploaded[0], 2)} {total_uploaded[1]}\n"
    if torrent.status == "stopped":
        start_stop = [
            telegram.InlineKeyboardButton(
                "▶️Start",
                callback_data=f"torrent_{torrent_id}_start",
            )
        ]
    else:
        start_stop = [
            telegram.InlineKeyboardButton(
                "⏹Stop",
                callback_data=f"torrent_{torrent_id}_stop",
            )
        ]
    reply_markup = telegram.InlineKeyboardMarkup(
        [
            start_stop,
            [
                telegram.InlineKeyboardButton(
                    "🗑Delete",
                    callback_data=f"deletemenutorrent_{torrent_id}",
                )
            ],
            [
                telegram.InlineKeyboardButton(
                    "📂Files",
                    callback_data=f"torrentsfiles_{torrent_id}",
                ),
                telegram.InlineKeyboardButton(
                    "🔄Reload",
                    callback_data=f"torrent_{torrent_id}_reload",
                ),
            ],
            [
                telegram.InlineKeyboardButton(
                    "⏪Back",
                    callback_data="torrentsgoto_0",
                )
            ],
        ]
    )
    return text, reply_markup


def get_files(torrent_id: int) -> Tuple[str, telegram.InlineKeyboardMarkup]:
    SIZE_OF_LINE = 45

    torrent = transClient.get_torrent(torrent_id)
    if len(torrent.name) >= SIZE_OF_LINE:
        name = f"{torrent.name[:SIZE_OF_LINE]}.."
    else:
        name = torrent.name
    text = f"{name}\n"
    text += "Files:\n"
    for file_id, file in enumerate(torrent.files()):
        raw_name = file.name.split("/")
        if len(raw_name) == 2:
            filename = raw_name[1]
        else:
            filename = file.name
        if len(filename) >= SIZE_OF_LINE:
            filename = f"{filename[:SIZE_OF_LINE]}.."
        text += f"{file_id+1}. {filename}  {round(utils.file_progress(file), 1)}%\n"
    reply_markup = telegram.InlineKeyboardMarkup(
        [
            [
                telegram.InlineKeyboardButton(
                    "🔄Reload",
                    callback_data=f"torrentsfiles_{torrent_id}_reload",
                )
            ],
            [
                telegram.InlineKeyboardButton(
                    "⏪Back",
                    callback_data=f"torrent_{torrent_id}",
                )
            ],
        ]
    )
    return text, reply_markup


def get_torrents(start_point: int = 0) -> Tuple[str, telegram.InlineKeyboardMarkup]:
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
                name = f"{torrent.name[:SIZE_OF_LINE]}.."
            else:
                name = torrent.name
            torrent_list += f"{count+1}. {name}   {STATUS_LIST[torrent.status]}\n"
            if column >= KEYBORD_WIDTH:
                keyboard.append(list())
                column = 0
                row += 1
            keyboard[row].append(
                telegram.InlineKeyboardButton(
                    f"{count+1}", callback_data=f"torrent_{torrent.id}"
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
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    return torrent_list, reply_markup


def delete_menu(torrent_id: int) -> Tuple[str, telegram.InlineKeyboardMarkup]:
    torrent = transClient.get_torrent(torrent_id)
    text = (
        "⚠️Do you really want to delete this torrent?⚠️\n"
        f"{torrent.name}\n"
        "You also can delete torrent with all downloaded data."
    )
    reply_markup = telegram.InlineKeyboardMarkup(
        [
            [
                telegram.InlineKeyboardButton(
                    "❌Yes❌",
                    callback_data=f"deletetorrent_{torrent_id}",
                )
            ],
            [
                telegram.InlineKeyboardButton(
                    "❌Yes, with data❌",
                    callback_data=f"deletetorrent_{torrent_id}_data",
                )
            ],
            [
                telegram.InlineKeyboardButton(
                    "⏪Back",
                    callback_data=f"torrent_{torrent_id}",
                )
            ],
        ]
    )
    return text, reply_markup


def add_menu(torrent_id: int) -> Tuple[str, telegram.InlineKeyboardMarkup]:
    torrent = transClient.get_torrent(torrent_id)
    text = "🆕Adding torrent🆕\n"
    text += f"{torrent.name}\n"
    text += "Files:\n"
    for file_id, file in enumerate(torrent.files()):
        raw_name = file.name.split("/")
        if len(raw_name) == 2:
            filename = raw_name[1]
        else:
            filename = file.name
        text += f"{file_id+1}. {filename}\n"
    free_memory = trans.utils.format_size(transClient.free_space(config.DISK))
    total_size = trans.utils.format_size(torrent.totalSize)
    size_when_done = trans.utils.format_size(torrent.sizeWhenDone)
    text += f"Total size: {round(total_size[0], 2)} {total_size[1]}\n"
    text += f"Chosen to download: {round(size_when_done[0], 2)} {size_when_done[1]}\n"
    text += f"Free disk space: {round(free_memory[0], 2)} {free_memory[1]}\n"
    reply_markup = telegram.InlineKeyboardMarkup(
        [
            [
                telegram.InlineKeyboardButton(
                    "▶️Start",
                    callback_data=f"torrentadd_{torrent_id}_start",
                ),
                telegram.InlineKeyboardButton(
                    "❌Cancel",
                    callback_data=f"torrentadd_{torrent_id}_cancel",
                ),
            ]
        ]
    )
    return text, reply_markup


def started_menu(torrent_id: int) -> Tuple[str, telegram.InlineKeyboardMarkup]:
    torrent = transClient.get_torrent(torrent_id)
    text = f"Torrent {torrent.name} started successfully\n"
    reply_markup = telegram.InlineKeyboardMarkup(
        [
            [
                telegram.InlineKeyboardButton(
                    "Open Torrent",
                    callback_data=f"torrent_{torrent_id}",
                )
            ]
        ]
    )
    return text, reply_markup

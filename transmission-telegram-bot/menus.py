import base64
from typing import Tuple

import telegram
import transmission_rpc as trans
import transmission_rpc.utils as trans_utils
from telegram.utils.helpers import escape_markdown

from . import config, utils

STATUS_LIST = {
    "downloading": "⏬",
    "seeding": "✅",
    "checking": "🔁",
    "check pending": "📡",
    "stopped": "🛑",
}


def transsmission_client(client: int = 0) -> Tuple[trans.Client, str, str, bool]:
    conn = config.TRANSMISSION_CLIENTS[client].copy()
    del conn["name"]
    try:
        tr = trans.Client(**conn)
    except:  # noqa: E722
        if client:
            re = list(transsmission_client())
            re[-1] = False
            return tuple(re)
        else:
            raise ValueError
    return (
        tr,
        tr.get_session().download_dir,
        config.TRANSMISSION_CLIENTS[client]["name"],
        True
    )


transClient, DISK, CURRENT_SERVER, _ = transsmission_client()


def change_server(client: int):
    global transClient
    global DISK
    global CURRENT_SERVER
    transClient, DISK, CURRENT_SERVER, success = transsmission_client(client)
    return success


def start_torrent(torrent_id: int):
    transClient.start_torrent(torrent_id)


def stop_torrent(torrent_id: int):
    transClient.stop_torrent(torrent_id)


def verify_torrent(torrent_id: int):
    transClient.verify_torrent(torrent_id)


def delete_torrent(torrent_id: int, data: bool = False):
    transClient.remove_torrent(torrent_id, delete_data=data)


def torrent_set_files(torrent_id: int, file_id: int, state: bool):
    transClient.set_files({torrent_id: {file_id: {"selected": state}}})


def add_torrent_with_file(file) -> trans.Torrent:
    encoded_file = base64.b64encode(file).decode("utf-8")
    torrent = transClient.add_torrent(encoded_file, paused=True)
    return torrent


def add_torrent_with_magnet(url) -> trans.Torrent:
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
    size_in_bytes = transClient.free_space(DISK)
    if size_in_bytes is not None:
        free_memory = trans_utils.format_size(size_in_bytes)
        formatted_memory = f"Free {round(free_memory[0], 2)} {free_memory[1]}"
    else:
        formatted_memory = "Something went wrong"
    return formatted_memory


def torrent_menu(torrent_id: int) -> Tuple[str, telegram.InlineKeyboardMarkup]:
    torrent = transClient.get_torrent(torrent_id)
    text = f"*{escape_markdown(torrent.name, 2)}*\n"
    if torrent.status != "checking":
        text += escape_markdown(
            f"{utils.progress_bar(torrent.progress)}  {(round(torrent.progress, 1))}% ",
            2,
        )
    else:
        text += escape_markdown(
            f"{utils.progress_bar(torrent.recheckProgress * 100)}  "
            f"{(round(torrent.recheckProgress * 100, 1))}% ",
            2,
        )
    text += f"{STATUS_LIST[torrent.status]}\n"
    if download := torrent.rateDownload:
        speed = trans_utils.format_speed(download)
        raw_text = (
            f"Time remaining: {utils.formated_eta(torrent)}\n"
            f"Download rate: {round(speed[0], 1)} {speed[1]}\n"
        )
        text += escape_markdown(raw_text, 2)
    if torrent.status != "seeding":
        downloaded_bytes: int = torrent.sizeWhenDone - torrent.leftUntilDone
        downloaded = trans_utils.format_size(downloaded_bytes)
        raw_text = f"Downloaded: {round(downloaded[0],2)} {downloaded[1]}\n"
        text += escape_markdown(raw_text, 2)
    if upload := torrent.rateUpload:
        speed = trans_utils.format_speed(upload)
        raw_text = f"Upload rate: {round(speed[0], 1)} {speed[1]}\n"
        text += escape_markdown(raw_text, 2)
    size_when_done = trans_utils.format_size(torrent.sizeWhenDone)
    total_size = trans_utils.format_size(torrent.totalSize)
    total_uploaded = trans_utils.format_size(torrent.uploadedEver)
    raw_text = (
        f"Size to download: {round(size_when_done[0], 2)} {size_when_done[1]}"
        f" / {round(total_size[0], 2)} {total_size[1]}\n"
    )
    raw_text += (
        f"Total ever uploaded: {round(total_uploaded[0], 2)} {total_uploaded[1]}\n"
    )
    text += escape_markdown(raw_text, 2)
    if torrent.status == "stopped":
        start_stop = telegram.InlineKeyboardButton(
            "▶️Start",
            callback_data=f"torrent_{torrent_id}_start",
        )
    else:
        start_stop = telegram.InlineKeyboardButton(
            "⏹Stop",
            callback_data=f"torrent_{torrent_id}_stop",
        )
    reply_markup = telegram.InlineKeyboardMarkup(
        [
            [
                telegram.InlineKeyboardButton(
                    "🗑Delete",
                    callback_data=f"deletemenutorrent_{torrent_id}",
                ),
                start_stop,
            ],
            [
                telegram.InlineKeyboardButton(
                    "🔁Verify",
                    callback_data=f"torrent_{torrent_id}_verify",
                ),
                telegram.InlineKeyboardButton(
                    "📂Files",
                    callback_data=f"torrentsfiles_{torrent_id}",
                ),
            ],
            [
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
    SIZE_OF_LINE = 100
    KEYBORD_WIDTH = 5
    torrent = transClient.get_torrent(torrent_id)
    if len(torrent.name) >= SIZE_OF_LINE:
        name = f"{torrent.name[:SIZE_OF_LINE]}.."
    else:
        name = torrent.name
    text = f"*{escape_markdown(name, 2)}*\n"
    text += "Files:\n"
    column = 0
    row = 0
    file_keyboard = [[]]
    for file_id, file in enumerate(torrent.files()):
        raw_name = file.name.split("/")
        if len(raw_name) == 2:
            filename = raw_name[1]
        else:
            filename = file.name
        if len(filename) >= SIZE_OF_LINE:
            filename = f"{filename[:SIZE_OF_LINE]}.."
        id = escape_markdown(f"{file_id+1}. ", 2)
        file_size_raw = trans_utils.format_size(file.size)
        file_completed_raw = trans_utils.format_size(file.completed)
        file_size = escape_markdown(
            f"{round(file_completed_raw[0], 2)} {file_completed_raw[1]}"
            f" / {round(file_size_raw[0], 2)} {file_size_raw[1]}",
            2,
        )
        file_progress = escape_markdown(f"{round(utils.file_progress(file), 1)}%", 2)
        if column >= KEYBORD_WIDTH:
            file_keyboard.append([])
            column = 0
            row += 1
        if file.selected:
            filename = escape_markdown(filename, 2, "PRE")
            text += f"*{id}*`{filename}`\n"
            button = telegram.InlineKeyboardButton(
                f"{file_id+1}. ✅",
                callback_data=f"editfile_{torrent_id}_{file_id}_0",
            )
        else:
            filename = escape_markdown(filename, 2)
            text += f"*{id}*~{filename}~\n"
            button = telegram.InlineKeyboardButton(
                f"{file_id+1}. ❌",
                callback_data=f"editfile_{torrent_id}_{file_id}_1",
            )
        text += f"Size: {file_size} {file_progress}\n"
        column += 1
        file_keyboard[row].append(button)
    delimiter = "".join(["-" for _ in range(60)])
    text += escape_markdown(f"{delimiter}\n", 2)
    total_size = trans_utils.format_size(torrent.totalSize)
    size_when_done = trans_utils.format_size(torrent.sizeWhenDone)
    text += escape_markdown(
        f"Size to download: {round(size_when_done[0], 2)} {size_when_done[1]}"
        f" / {round(total_size[0], 2)} {total_size[1]}",
        2,
    )
    control_buttons = [
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
    reply_markup = telegram.InlineKeyboardMarkup(file_keyboard + control_buttons)
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
    start_point = start_point if torrents[start_point:] else 0
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
            name = escape_markdown(name, 2)
            number = escape_markdown(f"{count+1}. ", 2)
            torrent_list += f"*{number}*{name}   {STATUS_LIST[torrent.status]}\n"
            if column >= KEYBORD_WIDTH:
                keyboard.append([])
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
            keyboard.append([])
            row += 1
            keyboard[row].append(
                telegram.InlineKeyboardButton(
                    "🔄Reload",
                    callback_data=f"torrentsgoto_{start_point}_reload",
                )
            )
            keyboard.append([])
            row += 1
            if start_point:
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
        keyboard.append([])
        row += 1
        keyboard[row].append(
            telegram.InlineKeyboardButton(
                "🔄Reload",
                callback_data=f"torrentsgoto_{start_point}_reload",
            )
        )
        keyboard.append([])
        row += 1
        if start_point and torrent_list:
            keyboard[row].append(
                telegram.InlineKeyboardButton(
                    "⏪Back",
                    callback_data=f"torrentsgoto_{start_point - SIZE_OF_PAGE}",
                )
            )
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    if not torrent_list:
        torrent_list = "Nothing to display"
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
    text = "🆕__Adding torrent__🆕\n"
    text += f"*{escape_markdown(torrent.name, 2)}*\n"
    size_in_bytes = transClient.free_space(DISK)
    total_size = trans_utils.format_size(torrent.totalSize)
    size_when_done = trans_utils.format_size(torrent.sizeWhenDone)
    raw_text = (
        f"Size to download: {round(size_when_done[0], 2)} {size_when_done[1]}"
        f" / {round(total_size[0], 2)} {total_size[1]}\n"
    )
    if size_in_bytes is not None:
        free_memory = trans_utils.format_size(size_in_bytes)
        raw_text += f"Free disk space: {round(free_memory[0], 2)} {free_memory[1]}\n"
    else:
        raw_text += "Could not get free disk space\n"
    text += escape_markdown(raw_text, 2)
    reply_markup = telegram.InlineKeyboardMarkup(
        [
            [
                telegram.InlineKeyboardButton(
                    "📂Files",
                    callback_data=f"selectfiles_{torrent_id}",
                )
            ],
            [
                telegram.InlineKeyboardButton(
                    "▶️Start",
                    callback_data=f"torrentadd_{torrent_id}_start",
                ),
                telegram.InlineKeyboardButton(
                    "❌Cancel",
                    callback_data=f"torrentadd_{torrent_id}_cancel",
                ),
            ],
        ]
    )
    return text, reply_markup


def select_files_add_menu(torrent_id: int) -> Tuple[str, telegram.InlineKeyboardMarkup]:
    SIZE_OF_LINE = 100
    KEYBORD_WIDTH = 5
    torrent = transClient.get_torrent(torrent_id)
    if len(torrent.name) >= SIZE_OF_LINE:
        name = f"{torrent.name[:SIZE_OF_LINE]}.."
    else:
        name = torrent.name
    text = f"*{escape_markdown(name, 2)}*\n"
    text += "Files:\n"
    column = 0
    row = 0
    file_keyboard = [[]]
    for file_id, file in enumerate(torrent.files()):
        raw_name = file.name.split("/")
        if len(raw_name) == 2:
            filename = raw_name[1]
        else:
            filename = file.name
        if len(filename) >= SIZE_OF_LINE:
            filename = f"{filename[:SIZE_OF_LINE]}.."
        id = escape_markdown(f"{file_id+1}. ", 2)
        filename = escape_markdown(filename, 2, "PRE")
        file_size_raw = trans_utils.format_size(file.size)
        file_size = escape_markdown(
            f"{round(file_size_raw[0], 2)} {file_size_raw[1]}", 2
        )
        if column >= KEYBORD_WIDTH:
            file_keyboard.append([])
            column = 0
            row += 1
        if file.selected:
            text += f"*{id}*`{filename}`  {file_size}\n"
            button = telegram.InlineKeyboardButton(
                f"{file_id+1}. ✅",
                callback_data=f"fileselect_{torrent_id}_{file_id}_0",
            )
        else:
            text += f"*{id}*~{filename}~  {file_size}\n"
            button = telegram.InlineKeyboardButton(
                f"{file_id+1}. ❌",
                callback_data=f"fileselect_{torrent_id}_{file_id}_1",
            )
        column += 1
        file_keyboard[row].append(button)
    total_size = trans_utils.format_size(torrent.totalSize)
    size_when_done = trans_utils.format_size(torrent.sizeWhenDone)
    text += escape_markdown(
        f"Size to download: {round(size_when_done[0], 2)} {size_when_done[1]}"
        f" / {round(total_size[0], 2)} {total_size[1]}",
        2,
    )
    control_buttons = [
        [
            telegram.InlineKeyboardButton(
                "⏪Back",
                callback_data=f"addmenu_{torrent_id}",
            )
        ],
    ]
    reply_markup = telegram.InlineKeyboardMarkup(file_keyboard + control_buttons)
    return text, reply_markup


def started_menu(torrent_id: int) -> Tuple[str, telegram.InlineKeyboardMarkup]:
    torrent = transClient.get_torrent(torrent_id)
    text = f"Torrent *{escape_markdown(torrent.name, 2)}* started successfully\n"
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


def settings_menu() -> Tuple[str, telegram.InlineKeyboardMarkup]:
    text = "Here is some bot settings:\n"
    reply_markup = telegram.InlineKeyboardMarkup(
        [
            [
                telegram.InlineKeyboardButton(
                    "Change transmission server",
                    callback_data="changeservermenu_0",
                )
            ]
        ]
    )
    return text, reply_markup


def change_server_menu(
    start_point: int = 0,
) -> Tuple[str, telegram.InlineKeyboardMarkup]:
    SIZE_OF_PAGE = 3
    text = f"Available servers:\nCurrent: {CURRENT_SERVER}"
    row = 0
    server_number = start_point
    keyboard = []
    for server in config.TRANSMISSION_CLIENTS[start_point:]:
        if row < SIZE_OF_PAGE:
            if server["name"] == CURRENT_SERVER:
                name = f"{server['name']} 🟢"
            else:
                name = server["name"]
            keyboard.append(
                [
                    telegram.InlineKeyboardButton(
                        name,
                        callback_data=f"server_{server_number}_{start_point}",
                    )
                ]
            )
            server_number += 1
            row += 1
        else:
            keyboard.append([])
            if start_point:
                keyboard[-1].append(
                    telegram.InlineKeyboardButton(
                        "⏪Back",
                        callback_data=f"changeservermenu_{start_point - SIZE_OF_PAGE}",
                    )
                )
            keyboard[-1].append(
                telegram.InlineKeyboardButton(
                    "Next⏩",
                    callback_data=f"changeservermenu_{row}",
                )
            )
            break
    else:
        if start_point:
            keyboard.append(
                [
                    telegram.InlineKeyboardButton(
                        "⏪Back",
                        callback_data=f"changeservermenu_{start_point - SIZE_OF_PAGE}",
                    )
                ]
            )
    keyboard.append(
        [
            telegram.InlineKeyboardButton(
                "⏪Back to Settings",
                callback_data="settings",
            )
        ]
    )
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    return text, reply_markup

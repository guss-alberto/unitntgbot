# /rooms ................ Mostra le aule libere e occupate del dipartimento di default (con una Warning che dice di poter cambiare il dipartimento di default)
# /rooms povo ........... Mostra le aule libere e occupate a Povo
# /rooms mesiano ........ Mostra le aule libere e occupate a Mesiano

import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.ext import ContextTypes

from unitntgbot.backend.rooms.Room import Event, Room

NAME_TO_BUILDING_ID = {
    # E0504
    "polo-tecnologico-rovereto": "E0504",
    "techrov": "E0504",
    "roveretotech": "E0504",
    "t": "E0504",
    # E0801
    "palazzo-prodi": "E0801",
    "prodi": "E0801",
    "lettere": "E0801",
    "l": "E0801",
    # E0601
    "sociologia": "E0601",
    "socio": "E0601",
    "s": "E0601",
    # E0502
    "bernardo-clesio": "E0502",
    "bernardo": "E0502",
    "clesio": "E0502",
    # E0503
    "povo": "E0503",
    "pov": "E0503",
    "rotta": "E0503",
    "p": "E0503",
    # E0901
    "san-michele": "E0901",
    "smichele": "E0901",
    "sm": "E0901",
    # E0705
    "psicologia": "E0705",
    "psico": "E0705",
    "rovereto": "E0705",
    "r": "E0705",
    # E1001
    "palazzo-consolati": "E1001",
    "consolati": "E1001",
    "economia": "E0101",
    "e": "E0101",
    # E0301
    "mesiano": "E0301",
    "mesi": "E0301",
    "dicam": "E0301",
    "m": "E0301",
    # E0201
    "giurisprudenza": "E0201",
    "giuri": "E0201",
    "g": "E0201",
    # CLA
    "cla": "CLA",
    # SOI
    "soi": "SOI",
}


async def _send_room_message(message: Message, data: dict, status_code: int) -> None:
    match status_code:
        case 404:
            await message.reply_text("University Room not found in department")
            return
        case 500:
            await message.reply_text("Internal server error")
            return
        case 200:
            capacity = f"_({data["capacity"]} seats)_" if data["capacity"] else ""
            msg = f"*Room {data["room_name"]} - {data["building_name"]}* {capacity} at {data["time"]}\n\n"

            rooms_formatted = [Event(*room).format() for room in data["room_data"]]
            msg += "\n".join(rooms_formatted)
            msg += " all day"
            await message.reply_markdown(msg)
            return


async def _send_rooms_message(message: Message, data: dict, status_code: int) -> None:
    keyboard = [
        [
            InlineKeyboardButton("✅ Sort by Time", callback_data="room:time"),
            InlineKeyboardButton("☑️ Sort by Name", callback_data="room:name"),
        ],
    ]  # TODO: Add more options such as filter for free, occupied or all rooms.
    reply_markup = InlineKeyboardMarkup(keyboard)

    match status_code:
        case 404:
            await message.reply_text("University Department not found. Somehow...")
            return
        case 500:
            await message.reply_text("Internal server error")
            return
        case 200:
            msg = f"*Rooms for {data["building_name"]}*\n\n"

            rooms_formatted = [Room(*room).format() for room in data["rooms"]]
            msg += "\n".join(rooms_formatted)

            await message.reply_markdown(msg, reply_markup=reply_markup)
            return


async def rooms_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    args = context.args
    if not args or args[0] not in NAME_TO_BUILDING_ID:
        await update.message.reply_markdown("Please provide a valid department name.")
        # TODO: Add default department name, it has to be stored in the database.
        return

    building_id = NAME_TO_BUILDING_ID[args[0].lower()]
    room_name = args[1] if len(args) > 1 else None

    api_url = f"http://127.0.0.1:5002/rooms/{building_id}" + (f"/{room_name}" if room_name is not None else "")
    response = requests.get(api_url)
    data = response.json()

    if room_name:
        await _send_room_message(update.message, data, response.status_code)
    else:
        await _send_rooms_message(update.message, data, response.status_code)


async def rooms_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    if not query or not query.data or not query.message:
        return

    # tg_id = query.message.chat.id
    # api_url = f"http://127.0.0.1:5002/rooms/{building_id}"
    # response = requests.get(api_url, params={"date": date.isoformat()})
    # data = response.json()

    # match response.status_code:
    #     case 400:
    #         await query.edit_message_text(data["message"])
    #         return
    #     case 200:
    #         message, reply_markup = format_output(date, data["lectures"])
    #         await query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    #         return
    #     case _:
    #         await query.edit_message_text("An unknown error occured")

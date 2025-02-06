# /rooms ................ Mostra le aule libere e occupate del dipartimento di default (con una Warning che dice di poter cambiare il dipartimento di default)
# /rooms povo ........... Mostra le aule libere e occupate a Povo
# /rooms mesiano ........ Mostra le aule libere e occupate a Mesiano

import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.constants import ParseMode
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


def _room_events(building_id:str, room: str) -> tuple[str, str]:
    api_url = f"http://127.0.0.1:5002/rooms/{building_id}/room"
    response = requests.get(api_url, params={"room_query": room})

    match response.status_code:
        case 404:
            return "University Room not found in department", ""
        case 500|400:
            return "Internal Server Error", ""
        case 200:
            data = response.json()
            capacity = f"_({data["capacity"]} seats)_" if data["capacity"] else ""
            msg = f"*Room {data["room_name"]} - {data["building_name"]}* {capacity} at {data["time"]}\n\n"

            rooms_formatted = [Event(*room).format() for room in data["room_data"]]
            msg += "\n".join(rooms_formatted)
            msg += " all day"
            return msg, data["room_code"]
    return "", ""


def _rooms_status(building_id: str, sort_time: bool = True) -> tuple[str, InlineKeyboardMarkup|None]:
    api_url = f"http://127.0.0.1:5002/rooms/{building_id}"
    response = requests.get(api_url)
    keyboard = [
        [
            InlineKeyboardButton(
                f"{"✅" if sort_time else ""} Sort by Time",
                callback_data=f"rooms:time:{building_id}",
            ),
            InlineKeyboardButton(
                f"{"" if sort_time else "✅"}  Sort by Name",
                callback_data=f"rooms:name:{building_id}",
            ),
        ],
    ]  # TODO: Add more options such as filter for free, occupied or all rooms.
    reply_markup = InlineKeyboardMarkup(keyboard)

    match response.status_code:
        case 404:
            return "University Department not found. Somehow...", None
        case 500:
            return "Internal Server Error", None
        case 200:
            data = response.json()

            msg = f"*Rooms for {data["building_name"]}* at {data["time"]}\n\n"

            rooms = [Room(*room) for room in data["rooms"]]

            rooms.sort(key=lambda r: r.name)
            if sort_time:
                # Port by time descendig if is free and ascending otherwise
                rooms.sort(key=lambda r: -r.time if r.is_free else r.time)
                # Put all "free all day" rooms on top
                rooms.sort(key=lambda r: r.time != 0)

            rooms_formatted = [room.format() for room in rooms]
            msg += "\n".join(rooms_formatted)

            return msg, reply_markup
    return "", None


async def rooms_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    args = context.args
    if not args or args[0] not in NAME_TO_BUILDING_ID:
        await update.message.reply_markdown("Please provide a valid department name.")
        # TODO: Add default department name, it has to be stored in the database.
        return

    building_id = NAME_TO_BUILDING_ID[args[0].lower()]
    room_name = " ".join(args[1:]) if len(args) > 1 else None

    if room_name:
        msg, room_code = _room_events(building_id, room_name)
        map_response = requests.get(f"http://127.0.0.1:5004/maps/{room_code}")
        if map_response.status_code == 200 and room_code:  # noqa: PLR2004
            await update.message.reply_photo(photo=map_response.content, caption=msg, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_markdown(msg+"\n\nMap not available for this room")
    else:
        msg, markup = _rooms_status(building_id)
        await update.message.reply_markdown(msg, reply_markup=markup)


async def rooms_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    if not query or not query.data or not query.message:
        return

    _, sort_type, building_id = query.data.split(":")

    msg, markup = _rooms_status(building_id, sort_time=sort_type=="time")

    await query.edit_message_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)

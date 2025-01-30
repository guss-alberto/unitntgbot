# /rooms ................ Mostra le aule libere e occupate del dipartimento di default (con una Warning che dice di poter cambiare il dipartimento di default)
# /rooms povo ........... Mostra le aule libere e occupate a Povo
# /rooms mesiano ........ Mostra le aule libere e occupate a Mesiano

import requests

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from unitntgbot.backend.rooms.Room import Room

NAME_TO_BUILDING_ID = {
    "polo-tecnologico-rovereto": "E0504",
    "techrov": "E0504",
    "roveretotech": "E0504",
    "t": "E0504",
    #
    "palazzo-prodi": "E0801",
    "prodi": "E0801",
    "lettere": "E0801",
    "l": "E0801",
    #
    "sociologia": "E0601",
    "socio": "E0601",
    "s": "E0601",
    #
    "bernardo clesio": "E0502",
    "bernardo": "E0502",
    #
    "povo": "E0503",
    "pov": "E0503",
    "rotta": "E0503",
    "p": "E0503",
    #
    "san-michele": "E0901",
    "smichele": "E0901",
    #
    "psicologia": "E0705",
    "psico": "E0705",
    "rovereto": "E0705",
    "r": "E0705",
    #
    "palazzo-consolati": "E1001",
    "consolati": "E1001",
    "economia": "E0101",
    "e": "E0101",
    #
    "mesiano": "E0301",
    "mesi": "E0301",
    "dicam": "E0301",
    "m": "E0301",
    #
    "giurisprudenza": "E0201",
    "giuri": "E0201",
    "g": "E0201",
    #
    "cla": "CLA",
    #
    "soi": "SOI",
}


async def rooms_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    args = context.args
    if not args or args[0] not in NAME_TO_BUILDING_ID:
        await update.message.reply_markdown("Please provide a valid department name.\n" "\n") # TODO: Add default department name, it has to be stored in the database.
        return

    building_id = NAME_TO_BUILDING_ID[args[0].lower()]
    
    api_url = f"http://127.0.0.1:5002/rooms/{building_id}"
    response = requests.get(api_url)
    data = response.json()

    keyboard = [
        [
            InlineKeyboardButton("✅ Sort by Time", callback_data="room:time"),
            InlineKeyboardButton("☑️ Sort by Name", callback_data="room:name"),
        ],
    ]  # TODO: Add more options such as filter for free, occupied or all rooms.
    reply_markup = InlineKeyboardMarkup(keyboard)

    match response.status_code:
        case 404:
            await update.message.reply_text("University Department not found. Somehow...")
            return
        case 200:
            message = f"*Rooms for {data["building_name"]}*\n\n"
            
            rooms_fromatted = [Room(*room).format() for room in data["rooms"]]
            message += "\n".join(rooms_fromatted)

            await update.message.reply_markdown(message, reply_markup=reply_markup)
            return


async def rooms_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    if not query or not query.data or not query.message:
        return

    # tg_id = query.message.chat.id
    # api_url = f"http://127.0.0.1:5001/lectures/{tg_id}"
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

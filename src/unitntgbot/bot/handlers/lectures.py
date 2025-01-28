# /menu .......... Mostra il menu del ristorante
# /menu dinner ... Mostra il menu del ristorante Cena (solo a Tommaso Gar)

import requests

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from unitntgbot.backend.lectures.UniversityLecture import UniversityLecture

async def add_lectures_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    args = context.args
    if not args:
        await update.message.reply_markdown("""\
Please provide a valid UniTrentoApp calendar link using `/addlectures <unitrentoapp_link>`.

It can be found in the top right corner of the '*Favourites*' tab in the '*Classes Timetable*' section in your app.

_Note that this removes all courses you are currently following on this Telegram Bot._\
""")
        return

    tg_id = update.message.chat_id
    unitrentoapp_link = args[0]

    api_url = f"http://127.0.0.1:5001/lectures/{tg_id}"
    response = requests.post(api_url, params={"unitrentoapp_link": unitrentoapp_link})
    data = response.json()

    match response.status_code:
        case 200:
            await update.message.reply_text(f"{data["number"]} courses addeed successfully!")
            return
        case 400:
            await update.message.reply_text(f"{data["message"]}\nPlease insert a valid UniTrentoApp calendar link.")
            return


async def get_lectures_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    args = context.args
    date = args[0] if args else None

    tg_id = update.message.chat_id
    api_url = f"http://127.0.0.1:5001/lectures/{tg_id}"
    response = requests.get(api_url, params={ "date": date })
    data = response.json()

    keyboard = [
        [
            InlineKeyboardButton("⬅️", callback_data="lect:"),
            InlineKeyboardButton("➡️", callback_data="lect:"),
        ],
        [
            InlineKeyboardButton("⏪", callback_data="lect:"),
            InlineKeyboardButton("Today", callback_data="lect:"),
            InlineKeyboardButton("⏩", callback_data="lect:"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    match response.status_code:
        case 200:
            lectures = data["lectures"]
            await update.message.reply_text(str(lectures), reply_markup=reply_markup)
            return
        case 400:
            await update.message.reply_text(data["message"])
            return
        case 404:
            await update.message.reply_markdown("""No coursed added to your account yet.

Use the command `/addlectures <unitrentoapp_link>` first.

The link can be found in the top right corner of the '*Favourites*' tab in the '*Classes Timetable*' section in UniTrentoApp.""")
            return


async def lectures_callback_handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    if not query:
        return

    await query.answer()

    keyboard = [
        [InlineKeyboardButton("Option 1", callback_data="a" * 6)],
        [InlineKeyboardButton("Option 2", callback_data="menu2")],
        [InlineKeyboardButton("Visit Website", url="https://example.com")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Respond to the button click based on callback data
    if query.data == "1":
        await query.edit_message_text(text="You selected Option 1.")
    elif query.data == "2":
        await query.edit_message_text(text="Option 2 selected", reply_markup=reply_markup)

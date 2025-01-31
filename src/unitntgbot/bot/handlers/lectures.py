# /menu .......... Mostra il menu del ristorante
# /menu dinner ... Mostra il menu del ristorante Cena (solo a Tommaso Gar)

from datetime import date, datetime, timedelta

import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from unitntgbot.backend.lectures.UniversityLecture import UniversityLecture


def format_output(date: date, lectures: list) -> tuple[str, InlineKeyboardMarkup]:
    keyboard = [
        [
            InlineKeyboardButton("⬅️", callback_data="lect:" + (date - timedelta(days=1)).isoformat()),
            InlineKeyboardButton("➡️", callback_data="lect:" + (date + timedelta(days=1)).isoformat()),
        ],
        [
            InlineKeyboardButton("⏪", callback_data="lect:" + (date - timedelta(days=7)).isoformat()),
            InlineKeyboardButton("Today", callback_data="lect:now"),
            InlineKeyboardButton("⏩", callback_data="lect:" + (date + timedelta(days=7)).isoformat()),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = f"*Lectures for {date.strftime("%A, %B %d, %Y")}*\n\n"
    if lectures:
        lectures = [UniversityLecture(*lec).format() for lec in lectures]
        message += "\n\n".join(lectures)
    else:
        message += "No lectures for this day."

    return message, reply_markup


async def get_lectures_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    args = context.args
    date_arg = args[0] if args else None

    tg_id = update.message.chat_id
    api_url = f"http://127.0.0.1:5001/lectures/{tg_id}"
    response = requests.get(api_url, params={"date": date_arg})
    data = response.json()

    match response.status_code:
        case 400:
            await update.message.reply_text(data["message"])
            return
        case 404:
            await update.message.reply_markdown(
                "No coursed added to your account yet.\n"
                "\n"
                "Use the command `/addlectures <unitrentoapp_link>` first.\n"
                "\n"
                "The link can be found in the top right corner of the '*Favourites*' tab in the '*Classes Timetable*' section in UniTrentoApp.",
            )
            return
        case 200:
            date = datetime.fromisoformat(date_arg).date() if date_arg else datetime.now().date()

            message, reply_markup = format_output(date, data["lectures"])
            await update.message.reply_markdown(message, reply_markup=reply_markup)
            return
        case _:
            await update.message.reply_text("An unknown error occured")


async def get_lectures_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    if not query or not query.data or not query.message:
        return

    if query.data == "lect:now":
        date = datetime.now().date()
    else:
        date = datetime.fromisoformat(query.data.split(":")[1]).date()

    tg_id = query.message.chat.id
    api_url = f"http://127.0.0.1:5001/lectures/{tg_id}"
    response = requests.get(api_url, params={"date": date.isoformat()})
    data = response.json()

    match response.status_code:
        case 400:
            await query.edit_message_text(data["message"])
            return
        case 200:
            message, reply_markup = format_output(date, data["lectures"])
            await query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
            return
        case _:
            await query.edit_message_text("An unknown error occured")

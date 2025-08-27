from datetime import date, datetime, timedelta

import httpx
from lectures.UniversityLecture import UniversityLecture
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot_frontend.settings import settings
from bot_frontend.utils import edit_message_text_without_changes


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

    message = f"<b>Lectures for {date.strftime('%A, %Y-%m-%d')}</b>\n\n"
    if lectures:
        lectures = [UniversityLecture(**lec).format() for lec in lectures]
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

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.LECTURES_SVC_URL}/lectures/{tg_id}",
            params={"date": date_arg},
            timeout=30,
        )

    match response.status_code:
        case 400:
            data = response.json()
            await update.message.reply_text(data["message"])
            return
        case 404:
            await update.message.reply_html(
                "No coursed added to your account yet.\n"
                "\n"
                "Use the command /setup first.\n"
                "\n"
                "The link can be found in the top right corner of the '<b>Favourites</b>' tab in the '<b>Classes Timetable</b>' section in UniTrentoApp.",
            )
            return
        case 200:
            data = response.json()
            date = datetime.fromisoformat(date_arg).date() if date_arg else datetime.now().date()

            message, reply_markup = format_output(date, data["lectures"])
            await update.message.reply_html(message, reply_markup=reply_markup)
            return
        case 500:
            await update.message.reply_text("Internal Server Error")
            return
        case _:
            await update.message.reply_text("An unknown error occured")


async def get_lectures_callback_handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    if not query or not query.data or not query.message:
        return

    if query.data == "lect:now":
        date = datetime.now().date()
    else:
        date = datetime.fromisoformat(query.data.split(":")[1]).date()

    tg_id = query.message.chat.id

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.LECTURES_SVC_URL}/lectures/{tg_id}",
            params={"date": date.isoformat()},
            timeout=30,
        )
    data = response.json()

    match response.status_code:
        case 400:
            await edit_message_text_without_changes(query, data["message"])
            return
        case 200:
            message, reply_markup = format_output(date, data["lectures"])
            await edit_message_text_without_changes(
                query,
                message,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup,
            )
            return
        case _:
            await edit_message_text_without_changes(query, "An unknown error occured")

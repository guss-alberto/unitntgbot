# /menu .......... Mostra il menu del ristorante
# /menu dinner ... Mostra il menu del ristorante Cena (solo a Tommaso Gar)

from datetime import datetime, timedelta
import requests

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from unitntgbot.backend.lectures.UniversityLecture import UniversityLecture


async def add_lectures_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    args = context.args
    if not args:
        await update.message.reply_markdown(
            "Please provide a valid UniTrentoApp calendar link using `/addlectures <unitrentoapp_link>`.\n"
            "\n"
            "It can be found in the top right corner of the '*Favourites*' tab in the '*Classes Timetable*' section in your app.\n"
            "\n"
            "_Note that this removes all courses you are currently following on this Telegram Bot._"
        )
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
                "The link can be found in the top right corner of the '*Favourites*' tab in the '*Classes Timetable*' section in UniTrentoApp."
            )
            return
        case 200:
            date = datetime.fromisoformat(date_arg).date() if date_arg else datetime.now().date()
            keyboard = [
                [
                    InlineKeyboardButton("⬅️", callback_data="lect:" + (date - timedelta(days=1)).isoformat()),
                    InlineKeyboardButton("➡️", callback_data="lect:" + (date + timedelta(days=1)).isoformat()),
                ],
                [
                    InlineKeyboardButton("⏪", callback_data="lect:" + (date - timedelta(days=7)).isoformat()),
                    InlineKeyboardButton("Today", callback_data="lect:"),
                    InlineKeyboardButton("⏩", callback_data="lect:" + (date + timedelta(days=7)).isoformat()),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            lectures = data["lectures"]
            
            message = f"*Lectures for {date.strftime("%A, %B %d")}*\n\n"
            if lectures:
                lectures = [UniversityLecture(*l) for l in lectures]

                message += "\n\n".join([l.format() for l in lectures])
            else:
                message += "No lectures for today."

            await update.message.reply_markdown(message, reply_markup=reply_markup)
            return
        case _:
            await update.message.reply_text("An unknown error occured")


async def get_lectures_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    if not query or not query.data or not query.message:
        return

    if len(query.data) > len("lect:"):
        date = datetime.fromisoformat(query.data.split(":")[1]).date()
    else:
        date = datetime.now().date()

    tg_id = query.message.chat.id
    api_url = f"http://127.0.0.1:5001/lectures/{tg_id}"
    response = requests.get(api_url, params={"date": date.isoformat()})
    data = response.json()

    match response.status_code:
        case 400:
            await query.edit_message_text(data["message"])
            return
        case 404:
            await query.edit_message_text(
                "No coursed added to your account yet.\n"
                "\n"
                "Use the command `/addlectures <unitrentoapp_link>` first.\n"
                "\n"
                "The link can be found in the top right corner of the '*Favourites*' tab in the '*Classes Timetable*' section in UniTrentoApp.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        case 200:
            keyboard = [
                [
                    InlineKeyboardButton("⬅️", callback_data="lect:" + (date - timedelta(days=1)).isoformat()),
                    InlineKeyboardButton("➡️", callback_data="lect:" + (date + timedelta(days=1)).isoformat()),
                ],
                [
                    InlineKeyboardButton("⏪", callback_data="lect:" + (date - timedelta(days=7)).isoformat()),
                    InlineKeyboardButton("Today", callback_data="lect:"),
                    InlineKeyboardButton("⏩", callback_data="lect:" + (date + timedelta(days=7)).isoformat()),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            lectures = data["lectures"]
            
            message = f"*Lectures for {date.strftime("%A, %B %d")}*\n\n"
            if lectures:
                lectures = [UniversityLecture(*l) for l in lectures]

                message += "\n\n".join([l.format() for l in lectures])
            else:
                message += "No lectures for today."

            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            return
        case _:
            await query.edit_message_text("An unknown error occured")
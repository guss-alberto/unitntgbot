# /menu .......... Mostra il menu del ristorante
# /menu lunch .... Mostra il menu del ristorante Pranzo
# /menu dinner ... Mostra il menu del ristorante Cena (solo a Tommaso Gar)

from datetime import date, datetime, timedelta

import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from typing import Literal

from telegram.constants import ParseMode

def format_output(date: date, msg: str, is_dinner: bool = False) -> tuple[str, InlineKeyboardMarkup]:
    callback = "menu:"+ ("dinner:" if is_dinner else "lunch:")
    keyboard = [
        [
            InlineKeyboardButton("⬅️", callback_data=callback + (date - timedelta(days=1)).isoformat()),
            InlineKeyboardButton("➡️", callback_data=callback + (date + timedelta(days=1)).isoformat()),
        ],
        [
            InlineKeyboardButton("⏪", callback_data=callback + (date - timedelta(days=7)).isoformat()),
            InlineKeyboardButton("Today", callback_data=callback + "now"),
            InlineKeyboardButton("⏩", callback_data=callback + (date + timedelta(days=7)).isoformat()),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = f"*{"Dinner" if is_dinner else "Lunch" } menu for {date.strftime("%A, %B %d, %Y")}*:\n\n"
    if msg:
        message += msg
    else:
        message += "NOT AVAILABLE"
    if not is_dinner:
        message += "\n®️ indicates the menu item is the choice for the 'ridotto' menu"
    return message, reply_markup


async def canteen_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args # TODO: Fix it to work with args

    if not update.message:
        return
    # IMPORTANT! USE 127.0.0.1 INSTEAD OF LOCALHOST OR THE REQUESTS ON WINDOWS WILL BE 3 SECONDS LONGER!!!
    response = requests.get("http://127.0.0.1:5000/menu/lunch/")

    if response.status_code != 200:  # noqa: PLR2004
        await update.message.reply_text("Internal Server Error")
        return

    data = response.json()

    message, markup = format_output(datetime.fromisoformat(data["date"]).date(), data["menu"])
    await update.message.reply_markdown_v2(message, reply_markup=markup)




async def canteen_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    if not query or not context or not query.data:
        return

    await query.answer()

    _, menu_type, date = query.data.split(":")
    if date == "now":
        date = ""

    api_url = f"http://127.0.0.1:5000/menu/{menu_type}/?date={date}"
    response = requests.get(api_url)

    if response.status_code != 200:  # noqa: PLR2004
        await query.edit_message_text("Internal Server Error")
        return

    data = response.json()

    message, markup = format_output(datetime.fromisoformat(data["date"]).date(), data["menu"], menu_type == "dinner")
    await query.edit_message_text(message, reply_markup=markup, parse_mode=ParseMode.MARKDOWN_V2)

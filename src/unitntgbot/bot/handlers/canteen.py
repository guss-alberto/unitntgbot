# /menu .......... Mostra il menu del ristorante
# /menu lunch .... Mostra il menu del ristorante Pranzo
# /menu dinner ... Mostra il menu del ristorante Cena (solo a Tommaso Gar)

from datetime import datetime
import requests

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


async def canteen_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args # TODO: Fix it to work with args

    # if args[1] == "dinner":
    #     return
    # else:

    now = datetime.now().strftime("%Y-%m-%d")

    # IMPORTANT! USE 127.0.0.1 INSTEAD OF LOCALHOST OR THE REQUESTS ON WINDOWS WILL BE 3 SECONDS LONGER!!!
    api_url = f"http://127.0.0.1:5000/lunch/{now}"
    response = requests.get(api_url)
    data = response.json()

    keyboard = [
        [
            InlineKeyboardButton("⬅️", callback_data="menu:" + data["prev"]),
            InlineKeyboardButton("➡️", callback_data="menu:" + data["next"]),
        ],
        [InlineKeyboardButton("Today", callback_data="menu:" + now)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(data["message"], reply_markup=reply_markup)


async def canteen_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    if not query:
        return

    await query.answer()

    date = query.data.split(":")[1] if query.data else datetime.now().strftime("%Y-%m-%d")

    api_url = f"http://127.0.0.1:5000/lunch/{date}"
    response = requests.get(api_url)
    data = response.json()

    keyboard = [
        [
            InlineKeyboardButton("⬅️", callback_data="menu:" + data["prev"]),
            InlineKeyboardButton("➡️", callback_data="menu:" + data["next"]),
        ],
        [InlineKeyboardButton("Today", callback_data="menu:" + date)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(data["message"], reply_markup=reply_markup)

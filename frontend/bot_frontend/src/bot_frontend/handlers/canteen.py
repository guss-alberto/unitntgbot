# /menu .......... Mostra il menu del ristorante
# /menu lunch .... Mostra il menu del ristorante Pranzo
# /menu dinner ... Mostra il menu del ristorante Cena (solo a Tommaso Gar)

from datetime import date, datetime, timedelta

import httpx
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot_frontend.settings import settings
from bot_frontend.utils import edit_message_text_without_changes


def format_output(date: date, msg: str, *, is_dinner: bool = False) -> tuple[str, InlineKeyboardMarkup]:
    callback = "menu:" + ("dinner:" if is_dinner else "lunch:")
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

    message = f"<b>{'Dinner' if is_dinner else 'Lunch'} menu for {date.strftime('%A, %Y-%m-%d')}</b>:\n\n"
    if msg:
        message += msg
    else:
        message += "NOT AVAILABLE"
    if "®️" in msg:
        message += "\n®️ indicates the menu item is the choice for the 'ridotto' menu"
    return message, reply_markup


async def canteen_handler(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{settings.CANTEEN_SVC_URL}/menu/lunch/", timeout=30)

    if response.status_code == 404:
        data = response.json()
        message, markup = format_output(datetime.fromisoformat(data["date"]).date(), "NOT AVAILABLE")

    elif response.status_code != 200:  # noqa: PLR2004
        await update.message.reply_text("Internal Server Error")
        return
    else:
        data = response.json()
        message, markup = format_output(datetime.fromisoformat(data["date"]).date(), data["menu"])

    await update.message.reply_html(message, reply_markup=markup)


async def dinner_canteen_handler(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{settings.CANTEEN_SVC_URL}/menu/dinner/", timeout=30)

    if response.status_code != 200:  # noqa: PLR2004
        await update.message.reply_text("Internal Server Error")
        return

    data = response.json()

    message, markup = format_output(datetime.fromisoformat(data["date"]).date(), data["menu"], is_dinner=True)
    await update.message.reply_html(message, reply_markup=markup)


async def canteen_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    if not query or not context or not query.data:
        return

    await query.answer()

    _, menu_type, date = query.data.split(":")
    if date == "now":
        date = ""

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{settings.CANTEEN_SVC_URL}/menu/{menu_type}/?date={date}", timeout=30)

    if response.status_code != 200:  # noqa: PLR2004
        await edit_message_text_without_changes(query, "Internal Server Error")
        return

    data = response.json()

    message, markup = format_output(
        datetime.fromisoformat(data["date"]).date(),
        data["menu"],
        is_dinner=menu_type == "dinner",
    )
    await edit_message_text_without_changes(query, message, reply_markup=markup, parse_mode=ParseMode.HTML)

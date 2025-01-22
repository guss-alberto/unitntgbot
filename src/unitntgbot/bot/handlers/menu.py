# /menu .......... Mostra il menu del ristorante
# /menu dinner ... Mostra il menu del ristorante Cena (solo a Tommaso Gar)

from telegram import Update
from telegram.ext import ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("", callback_data="menu1")],
        [InlineKeyboardButton("Option 2", callback_data="menu2")],
        [InlineKeyboardButton("Visit Website", url="https://example.com")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("Choose an option:", reply_markup=reply_markup)


async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    if not query:
        return

    await query.answer()

    keyboard = [
        [InlineKeyboardButton("Option 1", callback_data="menu1")],
        [InlineKeyboardButton("Option 2", callback_data="menu2")],
        [InlineKeyboardButton("Visit Website", url="https://example.com")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Respond to the button click based on callback data
    if query.data == "1":
        await query.edit_message_text(text="You selected Option 1.")
    elif query.data == "2":
        await query.edit_message_text(text="Option 2 selected", reply_markup=reply_markup)
    pass

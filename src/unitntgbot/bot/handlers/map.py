# /menu .......... Mostra il menu del ristorante
# /menu dinner ... Mostra il menu del ristorante Cena (solo a Tommaso Gar)

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


async def map_handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("a", callback_data="1")],
        [InlineKeyboardButton("Option 2", callback_data="2")],
        [InlineKeyboardButton("Visit Website", url="https://example.com")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("What do you want to setup?", reply_markup=reply_markup)


async def map_callback_handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
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

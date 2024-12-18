#!/usr/bin/env python3

import argparse
import os
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, CommandHandler


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    update.message.reply_markdown_v2()
    # await update.message.reply_text(f"Hello {update.effective_user.first_name}")

# Qui si può impostare il dipartimento di default
async def setup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass

# Define the start function with inline buttons
async def rooms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass
    # keyboard = [
    #     [InlineKeyboardButton("", callback_data="1")],
    #     [InlineKeyboardButton("Option 2", callback_data="2")],
    #     [InlineKeyboardButton("Visit Website", url="https://example.com")],
    # ]

    # reply_markup = InlineKeyboardMarkup(keyboard)

    # await update.message.reply_text("Choose an option:", reply_markup=reply_markup)

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass

# Callback function for handling button clicks
# async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     query = update.callback_query
#     await query.answer()

#     keyboard = [
#         [InlineKeyboardButton("Option 1", callback_data="1")],
#         [InlineKeyboardButton("Option 2", callback_data="2")],
#         [InlineKeyboardButton("Visit Website", url="https://example.com")],
#     ]

#     reply_markup = InlineKeyboardMarkup(keyboard)

#     # Respond to the button click based on callback data
#     if query.data == "1":
#         await query.edit_message_text(text="You selected Option 1.")
#     elif query.data == "2":
#         await query.edit_message_text(text="Option 2 selected", reply_markup=reply_markup)

# /rooms ................ Mostra le aule libere e occupate del dipartimento di default (con una Warning che dice di poter cambiare il dipartimento di default)
# /rooms povo ........... Mostra le aule libere e occupate a Povo
# /rooms mesiano ........ Mostra le aule libere e occupate a Mesiano
# /rooms povo A101 ...... Mostra le informazioni sull'aula A101 a Povo durante tutto il giorno

# /menu ................. Mostra il menu del ristorante
# /menu cena ............ Mostra il menu del ristorante Cena (solo a Tommaso Gar)
# /menu calendario ...... Scarica il PDF del calendario (da decidere)

def main() -> None:
    load_dotenv()
    TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")

    assert TELEGRAM_BOT_TOKEN is not None, "TELEGRAM_BOT_TOKEN is not set in .env file"

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("setup", setup))
    app.add_handler(CommandHandler("rooms", rooms))
    app.add_handler(CallbackQueryHandler(rooms_callback_handler, pattern="^rooms"))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(menu_callback_handler, pattern="^menu"))

    app.run_polling()


if __name__ == "__main__":
    main()

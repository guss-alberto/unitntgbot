#!/usr/bin/env python3

import argparse
import os
from dotenv import load_dotenv

from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler

# Handler functions from other files that the Telegram bot will use
from handlers.setup import setup_handler, setup_callback_handler
from handlers.rooms import rooms_handler, rooms_callback_handler
from handlers.menu import menu_handler, menu_callback_handler


def main() -> None:
    load_dotenv()
    TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")

    assert TELEGRAM_BOT_TOKEN is not None, "TELEGRAM_BOT_TOKEN is not set in .env file"

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("setup", setup_handler))
    app.add_handler(CallbackQueryHandler(setup_callback_handler, pattern="^setup"))
    app.add_handler(CommandHandler("rooms", rooms_handler))
    app.add_handler(CallbackQueryHandler(rooms_callback_handler, pattern="^rooms"))
    app.add_handler(CommandHandler("menu", menu_handler))
    app.add_handler(CallbackQueryHandler(menu_callback_handler, pattern="^menu"))

    app.run_polling()


if __name__ == "__main__":
    main()

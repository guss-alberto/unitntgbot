import os

from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler

from unitntgbot.bot.handlers.menu import menu_callback_handler, menu_handler
from unitntgbot.bot.handlers.rooms import rooms_callback_handler, rooms_handler

# Handler functions from other files that the Telegram bot will use
from unitntgbot.bot.handlers.setup import setup_callback_handler, setup_handler

load_dotenv()
TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")


def entrypoint() -> None:
    if not TELEGRAM_BOT_TOKEN:
        msg = "TELEGRAM_BOT_TOKEN is not set in .env file"
        raise ValueError(msg)

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("setup", setup_handler))
    app.add_handler(CallbackQueryHandler(setup_callback_handler, pattern=r"^setup"))
    app.add_handler(CommandHandler("rooms", rooms_handler))
    app.add_handler(CallbackQueryHandler(rooms_callback_handler, pattern=r"^rooms"))
    app.add_handler(CommandHandler("menu", menu_handler))
    app.add_handler(CallbackQueryHandler(menu_callback_handler, pattern=r"^menu"))

    app.run_polling()

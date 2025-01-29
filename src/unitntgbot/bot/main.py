import asyncio
import os

import telegram
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes

from .handlers.canteen import canteen_callback_handler, canteen_handler
from .handlers.exams import exams_callback_handler, exams_handler
from .handlers.help import help_handler
from .handlers.lectures import add_lectures_handler, get_lectures_handler, get_lectures_callback_handler
from .handlers.map import map_callback_handler, map_handler
from .handlers.rooms import rooms_callback_handler, rooms_handler
from .handlers.setup import setup_callback_handler, setup_handler
from .handlers.transports import transports_callback_handler, transports_handler


async def set_commands(bot: telegram.Bot) -> None:
    """
    Set the commands to show in the menu of the bot in the bottom left corner.

    Args:
        bot (telegram.Bot): The bot to set the commands to

    """
    await bot.set_my_commands(
        [
            telegram.BotCommand(command="setup", description="Setup the bot"),
            telegram.BotCommand(command="rooms", description="Show the available rooms"),
            telegram.BotCommand(command="map", description="Show the map of the university"),
            telegram.BotCommand(command="menu", description="Show the canteen menu"),
            telegram.BotCommand(command="transports", description="Show the transports"),
            telegram.BotCommand(command="lectures", description="Show the lectures"),
            telegram.BotCommand(command="exams", description="Show the exams"),
            telegram.BotCommand(command="help", description="Show the help message"),
        ],
    )


def entrypoint() -> None:
    load_dotenv()
    TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")

    if not TELEGRAM_BOT_TOKEN:
        msg = "TELEGRAM_BOT_TOKEN is not set in .env file"
        raise ValueError(msg)

    # Create the bot application
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Setup commands to show in the menu
    el = asyncio.get_event_loop()
    el.run_until_complete(set_commands(app.bot))

    # Add the handlers for the different commands
    app.add_handler(CommandHandler("exams", exams_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("lectures", get_lectures_handler))
    app.add_handler(CommandHandler("addlectures", add_lectures_handler))
    app.add_handler(CommandHandler("map", map_handler))
    app.add_handler(CommandHandler("menu", canteen_handler))
    app.add_handler(CommandHandler("rooms", rooms_handler))
    app.add_handler(CommandHandler("setup", setup_handler))
    app.add_handler(CommandHandler("transports", transports_handler))

    # app.add_handler(CallbackQueryHandler(exams_handler))
    # app.add_handler(CallbackQueryHandler(help_handler))
    # app.add_handler(CallbackQueryHandler(lectures_handler))
    # app.add_handler(CallbackQueryHandler(map_callback_handler, pattern=r".*"))
    # app.add_handler(CallbackQueryHandler(canteen_handler))
    # app.add_handler(CallbackQueryHandler(rooms_handler))
    # app.add_handler(CallbackQueryHandler(setup_handler))
    # app.add_handler(CallbackQueryHandler(transports_handler))
    app.add_handler(CallbackQueryHandler(canteen_callback_handler, pattern=r"^menu:"))
    # app.add_handler(CallbackQueryHandler(exams_callback_handler, pattern))
    # app.add_handler(CallbackQueryHandler(rooms_callback_handler, pattern))
    app.add_handler(CallbackQueryHandler(get_lectures_callback_handler, pattern=r"^lect:"))

    app.run_polling(poll_interval = 0.1, allowed_updates=Update.ALL_TYPES)

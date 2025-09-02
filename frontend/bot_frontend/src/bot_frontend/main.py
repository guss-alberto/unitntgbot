import telegram
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot_frontend.handlers.canteen import canteen_callback_handler, canteen_handler, dinner_canteen_handler
from bot_frontend.handlers.exams import exams_callback_handler, exams_handler
from bot_frontend.handlers.help import default_handler, departments_handler, help_handler, start_handler
from bot_frontend.handlers.lectures import get_lectures_callback_handler, get_lectures_handler
from bot_frontend.handlers.rooms import rooms_callback_handler, rooms_handler
from bot_frontend.handlers.setup import (
    cancel,
    refresh_lectures,
    # set_default_department,
    set_notification_time,
    set_notifications,
    set_unitrentoapp_token,
    setup_callback_handler,
    setup_handler,
)
from bot_frontend.handlers.tt import tt_callback_handler, tt_handler
from bot_frontend.settings import settings


async def set_commands(app: Application) -> None:
    """
    Set the commands to show in the menu of the bot in the bottom left corner.

    Args:
        app (telegram.ext.Application): The app containing the bot to set the commands to

    """
    await app.bot.set_my_commands(
        [
            telegram.BotCommand(command="setup", description="Setup the bot"),
            telegram.BotCommand(command="rooms", description="Show the available rooms"),
            telegram.BotCommand(command="menu", description="Show the canteen menu"),
            telegram.BotCommand(command="dinner", description="Show the canteen dinner menu"),
            telegram.BotCommand(command="tt", description="Show the Trentino Trasporti bus trips"),
            telegram.BotCommand(command="lectures", description="Show the lectures"),
            # telegram.BotCommand(command="courses", description="Show the courses you follow"),
            telegram.BotCommand(command="exams", description="Show the exams"),
            telegram.BotCommand(command="departments", description="Show the department names and aliases for /rooms"),
            telegram.BotCommand(command="help", description="Show the help message"),
        ],
    )


async def empty_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update or not update.callback_query:
        return

    await update.callback_query.answer()


def main() -> None:
    app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).post_init(set_commands).build()

    # filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

    # Add the handlers for the different commands
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("departments", departments_handler))
    app.add_handler(CommandHandler("exams", exams_handler))
    app.add_handler(CommandHandler("lectures", get_lectures_handler))
    # app.add_handler(CommandHandler("courses", get_courses_handler))
    app.add_handler(CommandHandler("menu", canteen_handler))
    app.add_handler(CommandHandler("dinner", dinner_canteen_handler))
    app.add_handler(CommandHandler("rooms", rooms_handler))
    app.add_handler(CommandHandler("locuspocus", rooms_handler))
    app.add_handler(CommandHandler("tt", tt_handler))
    app.add_handler(CommandHandler("povotrento", tt_handler))
    app.add_handler(CommandHandler("help", help_handler))

    # Handlers to for the UnitrentoApp setup process
    add_lectures = ConversationHandler(
        entry_points=[
            CommandHandler("setup", setup_handler),
            # CallbackQueryHandler(set_default_department, pattern=r"^setup:department:.*$"),
            CallbackQueryHandler(refresh_lectures, pattern=r"^setup:refresh_lectures$"),
            CallbackQueryHandler(set_notification_time, pattern=r"^setup:notifications:.*:.*$"),
            CallbackQueryHandler(set_notifications, pattern=r"^setup:notifications:.*$"),
            CallbackQueryHandler(setup_callback_handler, pattern=r"^setup:.*$"),
        ],
        states={
            0: [
                CommandHandler("cancel", cancel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_unitrentoapp_token),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(add_lectures)

    # Callback handlers for the inline buttons
    app.add_handler(CallbackQueryHandler(canteen_callback_handler, pattern=r"^menu:"))
    app.add_handler(CallbackQueryHandler(rooms_callback_handler, pattern=r"^rooms:"))
    app.add_handler(CallbackQueryHandler(exams_callback_handler, pattern=r"^exams:"))
    app.add_handler(CallbackQueryHandler(get_lectures_callback_handler, pattern=r"^lect:"))
    app.add_handler(CallbackQueryHandler(tt_callback_handler, pattern=r"^tt:"))
    app.add_handler(CallbackQueryHandler(empty_callback_handler))

    app.add_handler(MessageHandler(filters.ALL, default_handler))

    app.run_polling(allowed_updates=Update.ALL_TYPES)

# /setup ... Shows the setup menu

from enum import Enum

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


async def setup_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Courses", callback_data=SetupCallbackAction.COURSES)],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot_data

    if update.message:
        await update.message.reply_text("Choose an option:", reply_markup=reply_markup)


async def setup_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    if not query:
        return

    await query.answer()

    keyboard = [
        [InlineKeyboardButton("Courses", callback_data=SetupCallbackAction.COURSES)],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if query.data == SetupCallbackAction.COURSES:
        await query.edit_message_text(text="You selected Courses.")
    else:
        await query.edit_message_text(text="Invalid option selected", reply_markup=reply_markup)
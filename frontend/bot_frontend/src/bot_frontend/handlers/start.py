from telegram import Update
from telegram.ext import ContextTypes


async def start_handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_html("""
Hello! I am the unofficial UniTN Telegram Bot.
To get started, type /setup, or see what you can do with /help.""")

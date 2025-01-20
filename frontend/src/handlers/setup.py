# /setup ... Shows the setup menu

from telegram import Update
from telegram.ext import ContextTypes


async def setup_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass


async def setup_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass

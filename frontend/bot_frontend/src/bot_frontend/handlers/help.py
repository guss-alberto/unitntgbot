from telegram import Update
from telegram.ext import ContextTypes

HELP_MESSAGE = (
    "<b>Commands:</b>\n"
    "- <code>/setup</code> - Show the setup menu\n"
    "- <code>/help</code> - Show this message\n"
    "- <code>/menu</code> - Show the canteen lunch menu"
    "- <code>/dinner</code>: dinner - Show the restaurant menu for dinner (only at Tommaso Gar)\n'"
    "- <code>/rooms</code> - Show the available rooms\n"
    "- <code>/map &lt;site&gt; &lt;room&gt</code> - Show where the room is located\n"
    "- <code>/tt</code> - Show the Trentino Trasporti but trips\n"
    "- <code>/lectures</code> - Show the lectures for today\n"
    "- <code>/exams</code> - Show the exams\n"
    "- <code>/help</code> - Show the help message"
)


async def help_handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_html(HELP_MESSAGE)

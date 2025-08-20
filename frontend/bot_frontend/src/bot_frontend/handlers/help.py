from telegram import Update
from telegram.ext import ContextTypes

HELP_MESSAGE = (
    "<b>Commands:</b>\n"
    "- /setup - Show the setup menu\n"
    "- /help - Show this message\n"
    "- /menu &lt;arg&gt; - Show the restaurant menu. Arg can be \"lunch\" or \"dinner\". Defaults to lunch.\n"
    '"- /menu: dinner - Show the restaurant menu for dinner (only at Tommaso Gar)\n'
    "- /rooms - Show the available rooms\n"
    "- /map &lt;site&gt; &lt;room&gt; - Show where the room is located\n"
    "- /tt - Show the Trentino Trasporti but trips\n"
    "- /lectures - Show the lecture\n"
    "- /exams - Show the exams\n"
    "- /help - Show the help message"
)


async def help_handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_html(HELP_MESSAGE)

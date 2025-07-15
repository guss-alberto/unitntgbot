from telegram import Update
from telegram.ext import ContextTypes

HELP_MESSAGE = (
    "*Commands:*\n"
    "\\- /setup \\- Show the setup menu\n"
    "\\- /help \\- Show this message\n"
    '\\- /menu \\<arg\\> \\- Show the restaurant menu\\. Arg can be "lunch" or "dinner"\\. Defaults to lunch\\.\n'
    "\\- /menu: dinner \\- Show the restaurant menu for dinner \\(only at Tommaso Gar\\)\n"
    "\\- /rooms \\- Show the available rooms\n"
    "\\- /map <site> <room> \\- Show where the room is located\n"
    "\\- /tt \\- Show the Trentino Trasporti but trips\n"
    "\\- /lectures \\- Show the lecture\n"
    "\\- /exams \\- Show the exams\n"
    "\\- /help \\- Show the help message"
)


async def help_handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_markdown_v2(HELP_MESSAGE)

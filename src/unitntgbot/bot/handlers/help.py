# /menu .......... Mostra il menu del ristorante
# /menu dinner ... Mostra il menu del ristorante Cena (solo a Tommaso Gar)

from telegram import Update
from telegram.ext import ContextTypes

HELP_MESSAGE = """\
*Commands:*
- /setup: Show the setup menu
- /help: Show this message
- /menu <arg>: Show the restaurant menu. Arg can be "lunch" or "dinner". Defaults to lunch.
- /menu dinner: Show the restaurant menu for dinner (only at Tommaso Gar)
- /rooms description="Show the available rooms"),
- /map", description="Show the map of the university"),
- /transports", description="Show the transports"),
- /lectures", description="Show the lectures"),
- /exams", description="Show the exams"),
- /help", description="Show the help message"),
"""


async def help_handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_markdown_v2(HELP_MESSAGE)

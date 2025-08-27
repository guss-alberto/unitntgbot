from telegram import Update
from telegram.ext import ContextTypes

SOURCE_INFO = (
    "This bot is open source <a href = 'https://github.com/guss-alberto/unitntgbot'>github.com/guss-alberto/unitntgbot</a>\n\n"
    "<i>Made by:</i>\n"
    " <b>@itsAlisaa</b>\n"
    " <b>@EliaTomaselli</b>\n"
    " <b>@ardubev_16</b>\n"
)

DEPARTMENT_CODES = (
    "<b>Departmemnt names and aliases for</b> <code>/rooms</code>:\n"
    "-<b>Polo-Tecnologico-Rovereto</b>:\n"
    "  - <code>techrov</code>\n"
    "  - <code>roveretotech</code>\n"
    "  - <code>t</code>\n"
    "-<b>Palazzo-Prodi</b>:\n"
    "  - <code>prodi</code>\n"
    "  - <code>lettere</code>\n"
    "  - <code>l</code>\n"
    "-<b>Sociologia</b>:\n"
    "  -<code>socio</code>\n"
    "  -<code>s</code>\n"
    "-<b>Bernardo-Clesio</b>:\n"
    "  -<code>bernardo</code>\n"
    "  -<code>clesio</code>\n"
    "-<b>Polo-Fabio-Ferrari</b>:\n"
    "  -<code>povo</code>\n"
    "  -<code>pov</code>\n"
    "  -<code>p</code>\n"
    "-<b>San-Michele</b>:\n"
    "  -<code>smichele</code>\n"
    "  -<code>sm</code>\n"
    "-<b>Psicologia</b>:\n"
    "  -<code>psico</code>\n"
    "  -<code>rovereto</code>\n"
    "  -<code>r</code>\n"
    "-<b>Palazzo-Consolati</b>:\n"
    "  -<code>consolati</code>\n"
    "  -<code>economia</code>\n"
    "  -<code>e</code>\n"
    "-<b>Mesiano</b>:\n"
    "  -<code>mesi</code>\n"
    "  -<code>dicam</code>\n"
    "  -<code>m</code>\n"
    "-<b>Giurisprudenza</b>:\n"
    "  -<code>giuri</code>\n"
    "  -<code>g</code>\n"
    "-<b>CLA</b>:\n"
    "  -<code>cla</code>\n"
    "-<b>SOI</b>:\n"
    "  -<code>soi</code>\n"
)

HELP_MESSAGE = (
    "<b>Commands:</b>\n"
    "- /setup - Show the setup menu\n"
    "- /menu - Show the canteen lunch menu\n"
    "- /dinner - Show the dinner menu (only at Tommaso Gar)\n"
    "- /rooms <code>&lt;site&gt;</code> - Show the available rooms in the specified department\n"
    "- /rooms <code>&lt;site&gt; &lt;room&gt</code> - Shows all events for that particular room\n"
    "- /departments - Shows the list of department codes and aliases for the /rooms command\n"
    "- /tt - Show the Trentino Trasporti but trips\n"
    "- /lectures - Show the lectures for today\n"
    "- /exams <code>&lt;query&gt;- Search all exam call in Esse3\n"
    "- /help - Show this message\n\n"
) + SOURCE_INFO

START_MESSAGE = (
    "Hello! I am the <i>unofficial</i> UniTN Telegram Bot.\n"
    "To get started check out what you can do with /help, and personalize your options with /setup\n\n"
) + SOURCE_INFO


async def help_handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_html(HELP_MESSAGE)


async def start_handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_html(START_MESSAGE)

async def departments_handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_html(DEPARTMENT_CODES)

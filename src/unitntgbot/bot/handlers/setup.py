# /setup .............. Shows the setup menu

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


async def add_lectures_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    args = context.args
    if not args:
        await update.message.reply_markdown(
            "Please provide a valid UniTrentoApp calendar link using `/addlectures <unitrentoapp_link>`.\n"
            "\n"
            "It can be found in the top right corner of the '*Favourites*' tab in the '*Classes Timetable*' section in your app.\n"
            "\n"
            "_Note that this removes all courses you are currently following on this Telegram Bot._",
        )
        return

    tg_id = update.message.chat_id
    unitrentoapp_link = args[0]

    api_url = f"http://127.0.0.1:5001/lectures/{tg_id}"
    response = requests.post(api_url, params={"unitrentoapp_link": unitrentoapp_link})
    data = response.json()

    match response.status_code:
        case 200:
            await update.message.reply_text(f"{data["number"]} courses addeed successfully!")
            return
        case 400:
            await update.message.reply_text(f"{data["message"]}\nPlease insert a valid UniTrentoApp calendar link.")
            return


async def setup_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Lectures Token", callback_data="setup:lecture")],
        [InlineKeyboardButton("Default Department", callback_data="setup:department")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("Choose an option:", reply_markup=reply_markup)


async def setup_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    if not query or not query.message:
        return

    await query.answer()

    if query.data == "setup:lecture":
        update.callback_query.message.
    # if query.data == "setup:courses":
    #     await query.edit_message_text(text="You selected Courses.")
    # else:
    #     await query.edit_message_text(text="Invalid option selected", reply_markup=reply_markup)

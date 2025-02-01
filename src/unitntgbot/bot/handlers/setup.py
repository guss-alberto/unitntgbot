# /setup .............. Shows the setup menu

import requests

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler, CallbackContext


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
        [InlineKeyboardButton("Set Lectures Token", callback_data="setup:lecture")],
        [InlineKeyboardButton("Set Default Department", callback_data="setup:department")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("Choose an option:", reply_markup=reply_markup)


async def setup_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query

    if not query or not query.message:
        return ConversationHandler.END

    await query.answer()

    match query.data:
        case "setup:lecture":
            await query.edit_message_text("Write your UniTrentoApp token: (Type \"/cancel\" to cancel)")
            return 0
        case "setup:department":
            await query.edit_message_text("Write your default department: (Type \"/cancel\" to cancel)")
            return 1
        case _:
            await query.edit_message_text(text="Invalid option selected")
            return ConversationHandler.END


async def get_unitrentoapp_token(update: Update, context: CallbackContext) -> int:
    if not update.message:
        return ConversationHandler.END

    unitrentoapp_link = update.message.text
    tg_id = update.message.chat_id

    api_url = f"http://127.0.0.1:5001/lectures/{tg_id}"
    response = requests.post(api_url, params={"unitrentoapp_link": unitrentoapp_link})
    data = response.json()

    match response.status_code:
        case 200:
            await update.message.reply_text(f"{data["number"]} courses addeed successfully!")
            return ConversationHandler.END
        case 400:
            await update.message.reply_text(
                f'{data["message"]}\nPlease insert a valid UniTrentoApp calendar link. (Type "/cancel" to cancel)'
            )
            return 0

    return ConversationHandler.END


async def get_default_department(update: Update, context: CallbackContext) -> int:
    if not update.message:
        return ConversationHandler.END

    department = update.message.text

    print(department)

    await update.message.reply_text(f"Department saved successfully: {department}")
    return ConversationHandler.END


async def cancel(update: Update, context: CallbackContext) -> int:
    if not update.message:
        return ConversationHandler.END

    await update.message.reply_text("Canceled.")
    return ConversationHandler.END

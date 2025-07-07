# /setup .............. Shows the setup menu

import sqlite3

import httpx
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, ContextTypes, ConversationHandler

from unitntgbot.backend.rooms.rooms_mapping import BUILDING_ID_TO_NAME
from unitntgbot.bot.settings import settings


async def add_lectures_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    args = context.args
    if not args:
        await update.message.reply_markdown(
            "Please provide a valid UniTrentoApp calendar link using `/setup`.\n"
            "\n"
            "It can be found in the top right corner of the '*Favourites*' tab in the '*Classes Timetable*' section in your app.\n"
            "\n"
            "_Note that this removes all courses you are currently following on this Telegram Bot._",
        )
        return

    tg_id = update.message.chat_id
    unitrentoapp_link = args[0]

    # TODO: save on telegram bot db the unitrentoapp link and enable refreshing
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.LECTURES_SVC_URL}/lectures/{tg_id}",
            params={"unitrentoapp_link": unitrentoapp_link},
            timeout=30,
        )
    data = response.json()

    match response.status_code:
        case 200:
            await update.message.reply_text(f"{data['number']} courses addeed successfully!")
            return
        case 400:
            await update.message.reply_text(f"{data['message']}\nPlease insert a valid UniTrentoApp calendar link.")
            return


async def setup_handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Set Lectures Token", callback_data="setup:lecture")],
        [InlineKeyboardButton("Set Default Department", callback_data="setup:department")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("Choose an option:", reply_markup=reply_markup)


async def setup_callback_handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query

    if not query or not query.message:
        return ConversationHandler.END

    await query.answer()

    match query.data:
        case "setup:lecture":
            await query.edit_message_text(
                "Write your UniTrentoApp lectures link: \\(Type `/cancel` to cancel\\)"
                "\n"
                "It can be found in the top right corner of the '*Favourites*' tab in the '*Classes Timetable*' section in your app.\n"
                "\n"
                "_Note that this removes all courses you are currently following on this Telegram Bot._",
                parse_mode=ParseMode.MARKDOWN_V2,
            )
            return 0
        case "setup:department":
            keyboard = []
            for department_id, department_name in BUILDING_ID_TO_NAME.items():
                keyboard.append(
                    [InlineKeyboardButton(department_name, callback_data=f"setup:department:{department_id}")],
                )
            keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="setup:department:cancel")])
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text("Select your default department", reply_markup=reply_markup)
            return ConversationHandler.END
        case _:
            await query.edit_message_text(text="Invalid option selected")
            return ConversationHandler.END


async def get_unitrentoapp_token(update: Update, _: CallbackContext) -> int:
    if not update.message:
        return ConversationHandler.END

    unitrentoapp_link = update.message.text
    tg_id = update.message.chat_id

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.LECTURES_SVC_URL}/lectures/{tg_id}",
            params={"unitrentoapp_link": unitrentoapp_link},
            timeout=30,
        )

    match response.status_code:
        case 200:
            data = response.json()
            await update.message.reply_text(f"{data['number']} courses addeed successfully!")
            return ConversationHandler.END
        case 400:
            data = response.json()
            await update.message.reply_text(
                f'{data["message"]}\nPlease insert a valid UniTrentoApp calendar link. (Type "/cancel" to cancel)',
            )
            return 0
        case 500:
            await update.message.reply_text("Internal Server Error")
            return ConversationHandler.END

    return ConversationHandler.END


DEFAULT_DEPARTMENT_DATABASE = "db/settings.db"


async def get_default_department(update: Update, _: CallbackContext) -> int:
    query = update.callback_query
    if not update.effective_message or not query:
        return ConversationHandler.END

    data = query.data
    message = query.message
    if not data or not message:
        return ConversationHandler.END

    await query.answer()

    if data == "setup:department:cancel":
        await update.effective_message.edit_text("Operation canceled.")
        return ConversationHandler.END

    department_id = data[len("setup:department:") :]
    tg_id = message.chat.id

    db = sqlite3.connect(settings.DB_PATH)
    db.execute(
        """\
        CREATE TABLE IF NOT EXISTS DefaultDepartments (
            id TEXT NOT NULL PRIMARY KEY,
            department_id TEXT NOT NULL
        );""",
    )
    db.commit()
    db.execute("INSERT OR REPLACE INTO DefaultDepartments VALUES (?, ?);", (tg_id, department_id))
    db.commit()

    await update.effective_message.reply_text(f"Department saved successfully: {BUILDING_ID_TO_NAME[department_id]}")

    return ConversationHandler.END


async def cancel(update: Update, _: CallbackContext) -> int:
    if not update.message:
        return ConversationHandler.END

    await update.message.reply_text("Canceled.")
    return ConversationHandler.END

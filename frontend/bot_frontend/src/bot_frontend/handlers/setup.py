# /setup .............. Shows the setup menu

import re
import sqlite3

import httpx
from rooms.rooms_mapping import BUILDING_ID_TO_NAME
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, ContextTypes, ConversationHandler

from bot_frontend.settings import settings
from bot_frontend.utils import edit_message_text_without_changes

DB = sqlite3.connect(settings.DB_PATH)
# DB.execute(
#    """\
#    CREATE TABLE IF NOT EXISTS DefaultDepartments (
#        id TEXT PRIMARY KEY,
#        department_id TEXT NOT NULL
#    );""",
# )
DB.execute(
    """\
    CREATE TABLE IF NOT EXISTS LectureTokens (
        id TEXT PRIMARY KEY,
        token TEXT NOT NULL
    );""",
)
DB.commit()


MAIN_MENU_REPLY_MARKUP = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("🗓️ Link UniTrentoApp account", callback_data="setup:lecture")],
        [InlineKeyboardButton("🔄 Refresh Lectures", callback_data="setup:refresh_lectures")],
        # [InlineKeyboardButton("🏫 Set Default Department", callback_data="setup:department")],
        [InlineKeyboardButton("🔔 Notifications", callback_data="setup:notifications")],
    ],
)

NOTIFICATIONS_REPLY_MARKUP = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("🍝 Canteen", callback_data="setup:notifications:canteen")],
        [InlineKeyboardButton("🗓️ Lectures", callback_data="setup:notifications:lectures")],
        [InlineKeyboardButton("❌ Go Back", callback_data="setup:notifications:back")],
    ],
)


async def setup_handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text("Choose an option:", reply_markup=MAIN_MENU_REPLY_MARKUP)


async def setup_callback_handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int | None:
    query = update.callback_query

    if not query or not query.message:
        return ConversationHandler.END

    await query.answer()

    match query.data:
        case "setup:lecture":
            await edit_message_text_without_changes(
                query,
                "Write your <b>UniTrentoApp</b> lectures link: (Type <code>/cancel</code> to cancel)"
                "\n"
                "Your link can be found in 📤 the top right corner of the '<b>Favourites</b>' tab in the '<b>Classes Timetable</b>' section in your app.\n"
                "\n"
                "<i>Note that this removes all courses you are currently following on this Telegram Bot.</i>",
                parse_mode=ParseMode.HTML,
            )
            return 0
        # case "setup:department":
        #     keyboard = []
        #     for department_id, department_name in BUILDING_ID_TO_NAME.items():
        #         keyboard.append(
        #             [InlineKeyboardButton(department_name, callback_data=f"setup:department:{department_id}")],
        #         )
        #     keyboard.append([InlineKeyboardButton("❌ Go Back", callback_data="setup:department:back")])
        #     reply_markup = InlineKeyboardMarkup(keyboard)

        #     await edit_message_text_without_changes(query, "Select your default department", reply_markup=reply_markup)
        #     return ConversationHandler.END
        case "setup:refresh_lectures":
            # handled directly, shouldn't ever reach this point
            pass
        case "setup:notifications":
            await edit_message_text_without_changes(
                query,
                "Select the notifications you want to set up",
                reply_markup=NOTIFICATIONS_REPLY_MARKUP,
            )
            return ConversationHandler.END
        case _:
            await edit_message_text_without_changes(query, text="Invalid option selected")
            return ConversationHandler.END

    return ConversationHandler.END


async def set_unitrentoapp_token(update: Update, _: CallbackContext) -> int:
    if not update.message or not update.message.text:
        return ConversationHandler.END

    unitrentoapp_link = update.message.text
    tg_id = update.message.chat_id

    regex_full = r"(https:\/\/webapi\.unitn\.it\/unitrentoapp\/profile\/me\/calendar\/)?([A-F0-9]{64})"
    result = re.search(regex_full, unitrentoapp_link)
    if result:
        token = result.group(2)
    else:
        await update.message.reply_text('Please insert a valid UniTrentoApp calendar link. (Type "/cancel" to cancel)')
        return 0

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.LECTURES_SVC_URL}/courses/{tg_id}",
            json={"token": token},
            timeout=30,
        )

    match response.status_code:
        case 200:
            data = response.json()
            await update.message.reply_text(f"{data['number']} courses added successfully!")
            DB.execute("INSERT OR REPLACE INTO LectureTokens VALUES (?,?);", (tg_id, token))
            DB.commit()
        case _:
            await update.message.reply_text("An unknown error occurred while adding courses.")

    return ConversationHandler.END


async def set_default_department(update: Update, _: CallbackContext) -> int:
    query = update.callback_query
    if not update.effective_message or not query:
        return ConversationHandler.END

    data = query.data
    message = query.message
    if not data or not message:
        return ConversationHandler.END

    await query.answer()

    if data == "setup:department:back":
        await update.effective_message.edit_text("Choose an option:", reply_markup=MAIN_MENU_REPLY_MARKUP)
        return ConversationHandler.END

    department_id = data[len("setup:department:") :]
    tg_id = message.chat.id

    DB.execute("INSERT OR REPLACE INTO DefaultDepartments VALUES (?, ?);", (tg_id, department_id))
    DB.commit()

    await update.effective_message.edit_text(f"Department saved successfully: {BUILDING_ID_TO_NAME[department_id]}")

    return ConversationHandler.END


async def refresh_lectures(update: Update, _: CallbackContext) -> int:
    query = update.callback_query
    if not query or not query.message:
        return ConversationHandler.END

    await query.answer()
    tg_id = query.message.chat.id

    token = DB.execute(("SELECT token FROM LectureTokens WHERE id = ?;"), (tg_id,)).fetchone()

    if not token:
        await query.message.chat.send_message("You have not set your lectures token yet. Please do so first.")
        return ConversationHandler.END

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.LECTURES_SVC_URL}/courses/{tg_id}",
            params={"token": token},
            timeout=30,
        )

    match response.status_code:
        case 200:
            data = response.json()
            await edit_message_text_without_changes(query, f"{data['number']} courses refreshed successfully!")
        case _:
            await edit_message_text_without_changes(query, "An unknown error occurred while refreshing courses.")

    return ConversationHandler.END


async def set_notifications(update: Update, _: CallbackContext) -> int:
    query = update.callback_query
    if not update.effective_message or not query:
        return ConversationHandler.END

    data = query.data
    if not data:
        return ConversationHandler.END

    await query.answer()

    if data == "setup:notifications:back":
        await update.effective_message.edit_text("Choose an option:", reply_markup=MAIN_MENU_REPLY_MARKUP)
        return ConversationHandler.END

    notification_type = data[len("setup:notifications:") :]  # Either "canteen" or "lectures"

    keyboard = []
    row = []
    for hour in [
        "06:00",
        "06:30",
        "07:00",
        "07:30",
        "08:00",
        "08:30",
        "09:00",
        "09:30",
        "10:00",
        "10:30",
        "11:00",
        "11:30",
        "12:00",
        "12:30",
    ]:
        row.append(InlineKeyboardButton(hour, callback_data=f"setup:notifications:{notification_type}:{hour}"))

        # Make 2 per line
        if len(row) > 1:
            keyboard.append(row)
            row = []

    await edit_message_text_without_changes(
        query,
        f"Select the time for {notification_type} notifications",
        reply_markup=InlineKeyboardMarkup(
            [
                *keyboard,
                [InlineKeyboardButton("🔕 Disable", callback_data=f"setup:notifications:{notification_type}:disable")],
                [InlineKeyboardButton("❌ Go Back", callback_data=f"setup:notifications:{notification_type}:back")],
            ],
        ),
    )

    return ConversationHandler.END


async def set_notification_time(update: Update, _: CallbackContext) -> int:
    query = update.callback_query
    if not update.effective_message or not query:
        return ConversationHandler.END

    data = query.data
    message = query.message
    if not data or not message:
        return ConversationHandler.END

    await query.answer()

    if re.match(r"^setup:notifications:.*:back$", data):
        await edit_message_text_without_changes(
            query,
            "Select the notifications you want to set up",
            reply_markup=NOTIFICATIONS_REPLY_MARKUP,
        )
        return ConversationHandler.END

    notification_type, *time = data[len("setup:notifications:") :].split(":")
    time = ":".join(time)
    tg_id = message.chat.id

    if notification_type == "canteen":
        url = settings.CANTEEN_SVC_URL
    elif notification_type == "lectures":
        url = settings.LECTURES_SVC_URL
    else:
        return ConversationHandler.END

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{url}/{tg_id}/notification/",
            json={"time": time},
            timeout=30,
        )

        match response.status_code:
            case 200:
                data = response.json()
                await edit_message_text_without_changes(query, data.get("message"))
            case _:
                await edit_message_text_without_changes(query, "An unknown error occurred while setting notifications.")

    return ConversationHandler.END


async def cancel(update: Update, _: CallbackContext) -> int:
    if not update.message:
        return ConversationHandler.END

    await update.message.reply_text("Operation cancelled")
    return ConversationHandler.END

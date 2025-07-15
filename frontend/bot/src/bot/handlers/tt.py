import httpx
import json
from datetime import datetime
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from zoneinfo import ZoneInfo

from unitntgbot.bot.settings import settings


def generate_reply_markup(route: dict, sequence: int) -> InlineKeyboardMarkup:
    keyboard = [[]]

    if len(route) != 0 and sequence - 1 >= 0:
        keyboard[0].append(InlineKeyboardButton("⬅️", callback_data=f"tt:{sequence - 1}"))

    keyboard[0].append(InlineKeyboardButton("🔄", callback_data=f"tt:{sequence}"))

    totalRoutesCount = route.get("totalRoutesCount", 0)
    if len(route) != 0 and sequence + 1 < totalRoutesCount:
        keyboard[0].append(InlineKeyboardButton("➡️", callback_data=f"tt:{sequence + 1}"))

    reply_markup = InlineKeyboardMarkup(keyboard)

    if sequence != 0:
       keyboard.append([InlineKeyboardButton("Go back to first", callback_data=f"tt:0")])

    return reply_markup


def format_route(route: dict, sequence: int) -> str:
    markdown = f"*Trip {sequence + 1} of {route["totalRoutesCount"]}*:\n"
    markdown += "\n"
    current_hour = datetime.now().strftime("%H:%M")
    is_next = False
    current_stop_index = route["currentStopIndex"]
    stops = route.get("stops", [])
    for idx, stop in enumerate(stops):
        arrival_time = stop["arrivalTime"]
        stop_name = stop["stopName"]
       
        if current_stop_index is None:
            if not is_next and current_hour <= arrival_time:
                markdown += f"❓ *{arrival_time} - {stop_name}*\n"
                is_next = True
            else:
                markdown += f"⚪ {arrival_time} - {stop_name}\n"
        elif idx == current_stop_index:
          markdown += f"🚌 *{arrival_time} - {stop_name}*\n"
        elif idx < current_stop_index:
          markdown += f"🟡 {arrival_time} - {stop_name}\n"
        else:
          markdown += f"🟢 {arrival_time} - {stop_name}\n"


    markdown += "\n"
    if route["delay"] is not None:
        delay = int(route["delay"])
        if delay == 0:
            markdown += "*Bus is on time*\n"
        elif delay < 0:
            markdown += f"*{-delay} minute{"s" if delay != -1 else ""} early*\n"
        else:
            markdown += f"*{delay} minute{"s" if delay != 1 else ""} late*\n"

        if delay > 37:
            markdown += random.choice([
                "Is this bus operated by Trenitalia?\n",
                "Good luck\n",
                "Are we sure it's not on time for the next one\n",
                "Someone's getting fired (probably not)\n",
                "At this point, just walk\n",
                "Is it even moving?\n",
                "Have you checked they aren't on strike today?\n",
                "The wheels on the bus go round and round...\n",
            ])

        current_stop = route["stops"][route["currentStopIndex"]]["stopName"]
        markdown += f"Currently at _{current_stop}_\n"
        markdown += f"_Last updated {datetime.fromisoformat(route["lastUpdate"]).astimezone(ZoneInfo("Europe/Rome")).strftime("%H:%M")}_"
    else:
        markdown += "Real time data is not available at the moment"
        if "❓" in markdown:
            markdown += "\n\n❓ indicates where the bus should be right now"
    return markdown


async def tt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    async with httpx.AsyncClient() as client:
        # 400 is the routeId for the "5" bus that goes to Povo
        sequence = 0
        response = await client.get(f"{settings.TT_SVC_URL}/400/{sequence}", timeout=30)

        try:
          route = response.json()
        except json.JSONDecodeError:
          route = {}

        match response.status_code:
            case 200:
                markdown = format_route(route, sequence)
                reply_markup = generate_reply_markup(route, sequence)
                await update.message.reply_markdown(markdown, reply_markup=reply_markup)
                pass
            case _:
                reply_markup = generate_reply_markup(route, sequence)
                await update.message.reply_text("An unknown error occurred while fetching the bus route.", reply_markup=reply_markup)
                return


async def tt_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    if not query or not query.data or not query.message:
        return

    sequence = int(query.data.split(":")[1])
    
    async with httpx.AsyncClient() as client:
        # 400 is the routeId for the "5" bus that goes to Povo
        response = await client.get(f"{settings.TT_SVC_URL}/400/{sequence}", timeout=30)

        try:
          route = response.json()
        except json.JSONDecodeError:
          route = {}

        match response.status_code:
            case 200:
                markdown = format_route(route, sequence)
                reply_markup = generate_reply_markup(route, sequence)
                await query.edit_message_text(markdown, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
                pass
            case _:
                reply_markup = generate_reply_markup(route, sequence)
                await query.edit_message_text("An unknown error occurred while fetching the bus route.", reply_markup=reply_markup)
                return



    

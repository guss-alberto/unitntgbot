import json
import random
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot_frontend.settings import settings
from bot_frontend.utils import edit_message_text_without_changes


def generate_reply_markup(route: dict, sequence: int) -> InlineKeyboardMarkup:
    keyboard = [[], []]
    total_routes_count = route.get("totalRoutesCount", 0)

    if sequence > total_routes_count:
        # if out of range, show the back button only which goes to the second-to-last option
        keyboard[0].append(InlineKeyboardButton(" ", callback_data=" "))
        keyboard[0].append(InlineKeyboardButton("⬅️", callback_data=f"tt:{max(total_routes_count - 2, 0)}"))

        # TODO: this is awful, needs a rewrite
    else:
        if len(route) != 0 and sequence - 1 >= 0:
            keyboard[0].append(InlineKeyboardButton("⬅️", callback_data=f"tt:{sequence - 1}"))
        else:
            keyboard[0].append(InlineKeyboardButton(" ", callback_data=" "))

        if len(route) != 0 and sequence + 1 < total_routes_count:
            keyboard[0].append(InlineKeyboardButton("➡️", callback_data=f"tt:{sequence + 1}"))
        else:
            keyboard[0].append(InlineKeyboardButton(" ", callback_data=" "))

    if sequence != 0:
        keyboard[1].append(InlineKeyboardButton("⏪", callback_data="tt:0"))

    keyboard[1].append(InlineKeyboardButton("🔄", callback_data=f"tt:{sequence}"))

    return InlineKeyboardMarkup(keyboard)


def format_route(route: dict, sequence: int) -> str:
    html = f"<b>Trip {sequence + 1} of {route['totalRoutesCount']}</b>:\n"
    html += "\n"
    current_hour = datetime.now().strftime("%H:%M")
    is_next = False
    current_stop_index = route["currentStopIndex"]
    stops = route.get("stops", [])
    for idx, stop in enumerate(stops):
        arrival_time = stop["arrivalTime"]
        stop_name = stop["stopName"]

        if current_stop_index is None:
            if not is_next and current_hour <= arrival_time:
                html += f"❓ <b>{arrival_time} - {stop_name}</b>\n"
                is_next = True
            else:
                html += f"⚪ {arrival_time} - {stop_name}\n"
        elif idx == current_stop_index:
            html += f"🚌 <b>{arrival_time} - {stop_name}</b>\n"
        elif idx < current_stop_index:
            html += f"🟡 <i>{arrival_time} - {stop_name}</i>\n"
        else:
            html += f"🟢 {arrival_time} - {stop_name}\n"

    html += "\n"
    if route["delay"] is not None:
        delay = int(route["delay"])
        if delay == 0:
            html += "<b>Bus is on time</b>\n"
        elif delay < 0:
            html += f"<b>{-delay} minute{'s' if delay != -1 else ''} early</b>\n"
        else:
            html += f"<b>{delay} minute{'s' if delay != 1 else ''} late</b>\n"

        really_too_much_delay = 37
        if delay > really_too_much_delay:
            html += random.choice(
                [
                    "Is this bus operated by Trenitalia?\n",
                    "Good luck\n",
                    "Are we sure it's not on time for the next one\n",
                    "Someone's getting fired (probably not)\n",
                    "At this point, just walk\n",
                    "Is it even moving?\n",
                    "Have you checked they aren't on strike today?\n",
                    "The wheels on the bus go round and round...\n",
                ],
            )

        current_stop = route["stops"][route["currentStopIndex"]]["stopName"]
        html += f"Currently at <i>{current_stop}</i>\n"
        html += f"<i>Last updated {datetime.fromisoformat(route['lastUpdate']).astimezone(ZoneInfo('Europe/Rome')).strftime('%H:%M')}</i>"
    else:
        html += "Real time data is not available at the moment"
        if "❓" in html:
            html += "\n\n❓ indicates where the bus should be right now"
    return html


async def tt_handler(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
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

        reply_markup = generate_reply_markup(route, sequence)

        match response.status_code:
            case 200:
                html = format_route(route, sequence)
                await update.message.reply_html(html, reply_markup=reply_markup)
            case 204:
                await update.message.reply_text("No bus trips found for today", reply_markup=reply_markup)
            case _:
                await update.message.reply_text(
                    "An unknown error occurred while fetching the bus route.",
                    reply_markup=reply_markup,
                )
                return


async def tt_callback_handler(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
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
                html = format_route(route, sequence)
                reply_markup = generate_reply_markup(route, sequence)
                await edit_message_text_without_changes(
                    query,
                    html,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                )
            case _:
                reply_markup = generate_reply_markup(route, sequence)
                await edit_message_text_without_changes(
                    query,
                    "An unknown error occurred while fetching the bus route.",
                    reply_markup=reply_markup,
                )
                return

import httpx
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram import Update
from telegram.ext import ContextTypes

from unitntgbot.bot.settings import settings


def format_route(route: dict, sequence: int) -> tuple[str, InlineKeyboardMarkup]:
    markdown = f"*Trip {sequence} of {route['totaleCorseInLista']}*:\n"
    markdown += "\n"

    for stop in route["stops"]:
        arrival_time = stop["arrivalTime"]
        stop_name = stop["stopName"]
        markdown += f"🟢 {arrival_time} - {stop_name}\n"

    markdown += "\n"
    if route["delay"] is not None:
        markdown += f"\nDelay {route['delay']}\n"
    if route["lastEventRecivedAt"] is not None:
        current_stop = route["stops"][route["lastSequenceDetection"]]["stopName"]
        markdown += f"Currently at {current_stop}"

    keyboard = [[]]

    if sequence - 1 > 0:
        keyboard[0].append(InlineKeyboardButton("⬅️", callback_data=f"tt:{sequence - 1}"))

    keyboard[0].append(InlineKeyboardButton("🔄", callback_data=f"tt:{sequence}"))

    if sequence + 1 < route["totaleCorseInLista"]:
        keyboard[0].append(InlineKeyboardButton("➡️", callback_data=f"tt:{sequence + 1}"))

    reply_markup = InlineKeyboardMarkup(keyboard)

    return markdown, reply_markup


async def tt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    async with httpx.AsyncClient() as client:
        # 400 is the routeId for the "5" bus that goes to Povo
        response = await client.get(f"{settings.TT_SVC_URL}/400/1", timeout=30)
        route = response.json()

        match response.status_code:
            case 200:
                markdown, reply_markup = format_route(route, 1)
                await update.message.reply_markdown(markdown, reply_markup=reply_markup)
                pass
            case _:
                await update.message.reply_text("An unknown error occurred while fetching the bus route.")
                return


async def tt_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass

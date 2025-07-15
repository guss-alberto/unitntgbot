import httpx
from telegram import Update
from telegram.ext import ContextTypes

from bot_frontend.settings import settings


async def map_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            "Usage: /map <site_name> <room_code>\nExample: /map povo A201\nAvailable sites: povo, mesiano"
        )
        return

    site_name = args[0]
    room_code = args[1]

    if site_name == "povo":
        building_id = "E0503"
    elif site_name == "mesiano":
        building_id = "E0301"
    else:
        await update.message.reply_text("Invalid site name.")
        return

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.MAPS_SVC_URL}/maps/{building_id}", params={"rooms": room_code}, timeout=30
        )

        match response.status_code:
            case 400:
                data = response.json()
                await update.message.reply_text(data["message"])
            case 404:
                data = response.json()
                await update.message.reply_text(data["message"])
                return
            case 413:
                data = response.json()
                await update.message.reply_text(data["message"])
                return
            case 500:
                data = response.json()
                await update.message.reply_text(data["message"])
                return
            case 200:
                await update.message.reply_photo(photo=response.content, caption=f"Map for {site_name} - {room_code}")
                pass
            case _:
                await update.message.reply_text("An unknown error occurred while fetching the map.")
                return

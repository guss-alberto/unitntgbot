# /rooms ................ Mostra le aule libere e occupate del dipartimento di default (con una Warning che dice di poter cambiare il dipartimento di default)
# /rooms povo ........... Mostra le aule libere e occupate a Povo
# /rooms mesiano ........ Mostra le aule libere e occupate a Mesiano

import email
import io

import httpx
from rooms.Room import Event, Room
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from bot_frontend.settings import settings

NAME_TO_BUILDING_ID = {
    # E0504
    "polo-tecnologico-rovereto": "E0504",
    "techrov": "E0504",
    "roveretotech": "E0504",
    "t": "E0504",
    # E0801
    "palazzo-prodi": "E0801",
    "prodi": "E0801",
    "lettere": "E0801",
    "l": "E0801",
    # E0601
    "sociologia": "E0601",
    "socio": "E0601",
    "s": "E0601",
    # E0502
    "bernardo-clesio": "E0502",
    "bernardo": "E0502",
    "clesio": "E0502",
    # E0503
    "povo": "E0503",
    "pov": "E0503",
    "rotta": "E0503",
    "p": "E0503",
    # E0901
    "san-michele": "E0901",
    "smichele": "E0901",
    "sm": "E0901",
    # E0705
    "psicologia": "E0705",
    "psico": "E0705",
    "rovereto": "E0705",
    "r": "E0705",
    # E1001
    "palazzo-consolati": "E1001",
    "consolati": "E1001",
    "economia": "E0101",
    "e": "E0101",
    # E0301
    "mesiano": "E0301",
    "mesi": "E0301",
    "dicam": "E0301",
    "m": "E0301",
    # E0201
    "giurisprudenza": "E0201",
    "giuri": "E0201",
    "g": "E0201",
    # CLA
    "cla": "CLA",
    # SOI
    "soi": "SOI",
}


async def _room_events(building_id: str, room: str) -> tuple[str, str, InlineKeyboardMarkup | None]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.ROOMS_SVC_URL}/rooms/{building_id}/room",
            params={"room_query": room},
            timeout=30,
        )

    keyboard = [
        [
            InlineKeyboardButton(
                "🗺️ View Room Location",
                callback_data=f"rooms:s:{building_id}:{room}",
            ),
        ],
    ]  # TODO: Add more options such as filter for free, occupied or all rooms.
    reply_markup = InlineKeyboardMarkup(keyboard)

    match response.status_code:
        case 404:
            return "University Room not found in department", "", None
        case 500 | 400:
            return "Internal Server Error", "", None
        case 200:
            data = response.json()
            capacity = f"_({data['capacity']} seats)_" if data["capacity"] else ""
            msg = f"*Room {data['room_name']} - {data['building_name']}* {capacity} at {data['time']}\n\n"

            rooms_formatted = [Event(*room).format() for room in data["room_data"]]
            msg += "\n".join(rooms_formatted)
            msg += " all day"
            return msg, data["room_code"], reply_markup

    return "", "", None


# Returns a tuple with the message, the keyboard and the rooms map images
async def _rooms_status(
    building_id: str,
    *,
    sort_time: bool = True,
    with_images: bool = False,
) -> tuple[str, InlineKeyboardMarkup | None, list[bytes] | None]:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{settings.ROOMS_SVC_URL}/rooms/{building_id}", timeout=30)

    keyboard = [
        [
            InlineKeyboardButton(
                f"{'✅' if sort_time else ''} Sort by Time",
                callback_data=f"rooms:m:time:{building_id}",
            ),
            InlineKeyboardButton(
                f"{'' if sort_time else '✅'}  Sort by Name",
                callback_data=f"rooms:m:name:{building_id}",
            ),
        ],
    ]  # TODO: Add more options such as filter for free, occupied or all rooms.

    match response.status_code:
        case 200:
            data = response.json()

            msg = f"*Rooms for {data['building_name']}* at {data['time']}\n\n"

            rooms = [Room(*room) for room in data["rooms"]]

            rooms.sort(key=lambda r: r.name)
            if sort_time:
                # Sort by time descending if is free and ascending otherwise
                rooms.sort(key=lambda r: -r.time if r.is_free else r.time)
                # Put all "free all day" rooms on top
                rooms.sort(key=lambda r: r.time != 0)

            rooms_formatted = [room.format() for room in rooms]
            msg += "\n".join(rooms_formatted)

            free_rooms = [f"{building_id}/{room.name}" for room in rooms if room.is_free]

            if not free_rooms:
                msg += "\n\nNo free rooms available"

            images = None
            if with_images:
                images = []

                # Get the map for the free rooms
                async with httpx.AsyncClient() as client:
                    map_response = await client.get(
                        f"{settings.MAPS_SVC_URL}/maps/multi",
                        params={"rooms": ",".join(free_rooms)},
                        timeout=30,
                    )

                if map_response.status_code == 200:
                    # Retrieve the full raw response, including headers and body
                    raw_response = b"".join(
                        f"{key}: {value}\r\n".encode() for key, value in map_response.headers.items()
                    )
                    raw_response += b"\r\n"  # End of headers
                    raw_response += map_response.content  # The response body

                    # This method is used to parse multipart/mixed responses
                    # The response is a multipart response with multiple images
                    images_message = email.message_from_bytes(raw_response)
                    for index, images_part in enumerate(images_message.get_payload()):
                        # Get the image bytes
                        image_data = images_part.get_payload(decode=True)
                        images.append(image_data)

            # The map button should only show for buildings which have maps
            # and only if the message doesn't have maps already
            # also if no free rooms are available the button should not appear
            if not images and len(free_rooms) > 0 and building_id in ["E0503", "E0301"]:
                keyboard += (
                    [
                        InlineKeyboardButton(
                            "🗺️ View Free Rooms Location",
                            callback_data=f"rooms:m:{'time' if sort_time else 'name'}:{building_id}:map",
                        ),
                    ],
                )

            return msg, InlineKeyboardMarkup(keyboard), images

        case 404:
            return "University Department not found. Somehow...", None, None
        case _:
            return "Internal Server Error", None, None


async def rooms_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    args = context.args
    if not args or args[0] not in NAME_TO_BUILDING_ID:
        await update.message.reply_markdown("Please provide a valid department name.")
        # TODO: Add default department name, it has to be stored in the database.
        return

    building_id = NAME_TO_BUILDING_ID[args[0].lower()]
    room_name = " ".join(args[1:]) if len(args) > 1 else None

    # If the room_name was provided reply with the events for that room
    # Otherwise reply with the status of all rooms
    if room_name:
        msg, room_code, markup = await _room_events(building_id, room_name)
        await update.message.reply_markdown(msg, reply_markup=markup)
    else:
        msg, markup, images = await _rooms_status(building_id)
        await update.message.reply_markdown(msg, reply_markup=markup)


async def rooms_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    if not query or not query.data or not query.message:
        return

    rooms_args = query.data.split(":")

    # It was called from single room event
    if rooms_args[1] == "s":
        building_id = rooms_args[2]
        room_code = rooms_args[3]

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.MAPS_SVC_URL}/maps/{building_id}/{room_code}", timeout=30)
        if response.status_code == 200 and room_code:  # noqa: PLR2004
            await query.message.chat.send_photo(photo=response.content, caption=f"Location of room {room_code}")
        else:
            await query.message.chat.send_message("Map not available for this room")
    # It was called from the rooms status
    elif rooms_args[1] == "m":
        sort_type = rooms_args[2]
        building_id = rooms_args[3]
        with_images = len(rooms_args) > 4 and rooms_args[4] == "map"

        msg, markup, images = await _rooms_status(building_id, sort_time=sort_type == "time", with_images=with_images)

        try:
            # Telegram will raise an error if the message is not modified
            # which is the case when the user clicks on the button to show the map immediately after fetching the rooms status
            await query.edit_message_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)
        except BadRequest as e:
            if "Message is not modified" not in e.message:
                raise

        if images:
            media = [InputMediaPhoto(io.BytesIO(img)) for img in images]
            await query.message.chat.send_media_group(media, caption="Rooms status (the rooms in red are free)")

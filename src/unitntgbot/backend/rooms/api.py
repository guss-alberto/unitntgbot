from datetime import datetime

import pandas as pd
from flask import Flask, Response, jsonify, request
from fuzzywuzzy import process

from .Room import Event, Room
from .rooms_mapping import BUILDING_ID_TO_NAME
from .scraper import get_rooms as scraper_get_rooms

app = Flask(__name__)


def process_room(
    get_rooms_result: tuple[pd.DataFrame, pd.DataFrame | None, int],
    room: str,
    date: datetime,
) -> tuple[list[Event], str, str, int] | None:
    df_rooms, df_events, last_update_unix = get_rooms_result

    # Use fuzzy matching to find the closest room name
    room_names: list[str] = list(df_rooms["name"])
    closest_match = process.extractOne(room, room_names, score_cutoff=60)

    if not closest_match:
        return None  # 404 room not found

    closest_match = str(closest_match[0])
    room_s = df_rooms[df_rooms["name"] == closest_match].iloc[0]
    capacity = int(room_s["capacity"])

    if df_events is None:
        return [Event("", 0, is_free=True)], closest_match, room_s["room_code"], capacity

    room_events = df_events[
        (df_events["CodiceAula"] == room_s["room_code"])
        & (df_events["timestamp_to"] > date.timestamp())
        & (df_events["Annullato"] == "0")
    ]

    output: list[Event] = []
    time: int = 0
    if room_events[room_events["timestamp_from"] < date.timestamp()].empty:
        output.append(Event("", 0, is_free=True))

    for _, event in room_events.iterrows():
        event_name = event["utenti"] or event["nome"]

        # If we have a previous event and the current one starts more than 15 minutes after it, add the free time
        if time and event["timestamp_from"] > time + 15 * 60:
            output.append(Event("", time, is_free=True))

        output.append(Event(event_name, int(event["timestamp_from"]), is_free=False))

        time = int(event["timestamp_to"])

    # Add final empty block to signal room will be free all day
    if not output[-1].is_free:
        output.append(Event("", time, is_free=True))
    return output, closest_match, room_s["room_code"], capacity


def get_next_event(future_events: pd.DataFrame) -> int:
    # If it's free now we need to find the next event (if any) that happens in that room
    for _, event in future_events.iterrows():
        if event["Annullato"] == "0":  # Check if the event is cancelled before going through
            # If an event is found update time and name
            return event["timestamp_from"]
    # If no event is found return 0
    return 0


def get_next_gap(future_events: pd.DataFrame, time: int) -> int:
    # If the room occupied we need to find the next gap where the room is free, which will always be present
    for _, event in future_events.iterrows():
        # If an event is cancelled we know the room is free just after the current event
        # Otherwise we have to check if the event starts within 15 minutes before the room clears
        # If the next event doesn't start immediately we know there's a gap
        if event["Annullato"] == "1" or event["timestamp_from"] > time + 15 * 60:
            return time
        # if the event has no gap and isn't cancelled we need to set the time variable to the end so we can see if there is a gap with the next event
        time = event["timestamp_to"]
    return time


def process_building(get_rooms_result: tuple[pd.DataFrame, pd.DataFrame | None, int], date: datetime) -> list[Room]:
    df_rooms, df_events, last_update_unix = get_rooms_result
    rooms: list[Room] = []

    # Might return nothing as all rooms are free
    if df_events is None:
        return [Room(row["name"], row["capacity"], is_free=True, event="", time=0) for _, row in df_rooms.iterrows()]

    for _, row in df_rooms.iterrows():
        is_free = True
        event_name = ""
        time = 0
        room_events = df_events[
            (df_events["CodiceAula"] == row["room_code"]) & (df_events["timestamp_to"] > date.timestamp())
        ]

        # Check if the current room event, whether it is free right now, and if not, when the event ends
        current_event = room_events[room_events["timestamp_from"] < date.timestamp()]
        if not current_event.empty:
            current_event = current_event.iloc[0]
            event_name = current_event["utenti"] or current_event["nome"]
            if current_event["Annullato"] == "0":
                is_free = False
                time = current_event["timestamp_to"]

        future_events = room_events[room_events["timestamp_from"] > date.timestamp()]

        time = get_next_event(future_events) if is_free else get_next_gap(future_events, time)

        rooms.append(Room(row["name"], row["capacity"], is_free, event_name, int(time)))
    return rooms


@app.route("/rooms/<string:building_id>")
def get_rooms(building_id: str) -> tuple[Response, int]:
    result = scraper_get_rooms(building_id)

    if not result:
        return jsonify({"message": "Building ID Not Found"}), 404

    date = datetime.now()

    rooms = process_building(result, date)

    return jsonify(
        {"building_name": BUILDING_ID_TO_NAME[building_id], "time": date.strftime("%H:%M"), "rooms": rooms},
    ), 200


@app.route("/rooms/<string:building_id>/room")
def get_room(building_id: str) -> tuple[Response, int]:
    room_name = request.args.get("room_query")
    print(room_name)
    if not room_name:
        return jsonify({"message": "Room name not provided in `room_query` param"}), 400

    result = scraper_get_rooms(building_id)

    if not result:
        return jsonify({"message": "Building ID Not Found"}), 404

    date = datetime.now()

    room_name = room_name.upper()
    room_data = process_room(result, room_name, date)

    if room_data is None:
        return jsonify({"message": "Room Not Found"}), 404

    room_data, actual_name, room_code, capacity = room_data
    return jsonify(
        {
            "building_name": BUILDING_ID_TO_NAME[building_id],
            "room_name": actual_name,
            "room_code": room_code,
            "capacity": capacity,
            "time": date.strftime("%H:%M"),
            "room_data": room_data,
        },
    ), 200


def entrypoint() -> None:
    app.run(port=5002, debug=True)


# room: name, capacity, is_free, event, time

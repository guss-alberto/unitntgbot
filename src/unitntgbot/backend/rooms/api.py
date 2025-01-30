from datetime import datetime
from flask import Flask, Response, jsonify

from .rooms_mapping import BUILDING_ID_TO_NAME
from .scraper import get_rooms as scraper_get_rooms
from .Room import Room


app = Flask(__name__)


@app.route("/rooms/<string:building_id>")
def get_rooms(building_id: str) -> tuple[Response, int]:
    result = scraper_get_rooms(building_id)

    if not result:
        return jsonify({"message": "Building ID Not Found"}), 404

    df_rooms, df_events_current, df_events_future = result
    rooms: list[Room] = []

    for _, row in df_rooms.iterrows():
        room_name = row["name"]
        capacity = row["capacity"]

        is_free = True
        event_name = ""
        time = 0

        # Best code so far, prepare to be amazed \s 🤓
        # Check if the current room event, whether it is free right now, and if not, when the event ends
        current_event_row = df_events_current[df_events_current["CodiceAula"] == row["room_code"]]
        if not current_event_row.empty:
            current_event_row = current_event_row.iloc[0]
            event_name = current_event_row["utenti"] or current_event_row["nome"]
            if current_event_row["Annullato"] == "0":
                is_free = False
                time = current_event_row["timestamp_to"]

        future_event_row = df_events_future[df_events_future["CodiceAula"] == row["room_code"]].sort_values(
            "timestamp_from"
        )
        if is_free:
            # If it's free now we need to find the next event (if any) that happens in that room
            for _, event in future_event_row.iterrows():
                if event["Annullato"] == "0":  # Check if the event is cancelled before going through
                    # If an event is found update time and name
                    time = event["timestamp_from"]
                    event_name = event["utenti"] or event["nome"]
                    break
                # If no event is found time is never updated and stays at 0
        else:
            # If the room occupied we need to find the next gap where the room is free, which will always be present
            for _, event in future_event_row.iterrows():
                # If an event is cancelled we can just use the start time of that event as the room is free
                # Otherwise we have to check if the lecture starts at the same time the previous one ends
                # Since we only check this if the lecture is not cancelled we know the "time" variable is set to the end of the current event
                # If the next event doesn't start immediately we know there's a gap
                if event["Annullato"] == "1" or event["timestamp_from"] != time:
                    time = event["timestamp_from"]
                    break
                # if the event has no gap and isn't cancelled we need to set the time variable to the end so we can see if there is a gap with the next event
                time = event["timestamp_to"]

        # Format time to a huamn readable format if exists, othwerise the room is free all day and we can leave an empty string
        if time:
            time_str = datetime.fromtimestamp(time).strftime("%H:%M")
        else:
            time_str = ""

        room = Room(room_name, capacity, is_free, event_name, time_str)
        rooms.append(room)

    # print(rooms)

    return jsonify({"building_name": BUILDING_ID_TO_NAME[building_id], "rooms": rooms}), 200
    # return jsonify({}), 200


def entrypoint() -> None:
    app.run(port=5002, debug=True)


# room: name, capacity, is_free, event, time

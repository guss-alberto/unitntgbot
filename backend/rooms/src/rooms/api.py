from datetime import datetime

from flask import Flask, Response, jsonify, request

from rooms.rooms_mapping import BUILDING_ID_TO_NAME
from rooms.scraper import get_rooms as scraper_get_rooms

from .process_rooms import process_building, process_room

app = Flask(__name__)


@app.get("/rooms/<string:building_id>")
def get_rooms(building_id: str) -> tuple[Response, int]:
    result = scraper_get_rooms(building_id)

    if not result:
        return jsonify({"message": "Building ID Not Found"}), 404

    date = datetime.now()

    rooms = process_building(result, date)

    return jsonify(
        {"building_name": BUILDING_ID_TO_NAME[building_id], "time": date.strftime("%H:%M"), "rooms": [r._asdict() for r in rooms]},
    ), 200


@app.get("/rooms/<string:building_id>/room")
def get_room(building_id: str) -> tuple[Response, int]:
    room_name = request.args.get("room_query")
    # print(room_name)
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
            "room_data": [r._asdict() for r in room_data],
        },
    ), 200


def main() -> None:
    app.run("0.0.0.0")  # noqa: S104


def develop(port: int) -> None:
    app.run(port=port, debug=True)  # noqa: S201


# room: name, capacity, is_free, event, time

from collections import defaultdict

from flask import Flask, Response, jsonify, make_response, request

from .maps_service import get_map_path, render_room_map

app = Flask(__name__)


@app.get("/maps/<string:building_id>/<string:room_ids>")
def get_map_single(building_id: str, room_ids: str) -> tuple[Response | str, int]:
    """
    Return a png image containing the highlited rooms that could be found.

    The function assumes all roomsa are in the same floor, and if they aren't,
    it will only render those in the same floor as the first one.
    """
    rooms = room_ids.split("|")
    if len(rooms) > 30:
        return "Too many rooms were provided", 413  # HTTP code for payload too large

    path = get_map_path(building_id, rooms[0])
    if not path:
        return "Room not found or building not available", 404

    image = render_room_map(path, set(rooms))
    if not image:
        return "An unknown error occured", 500

    response = make_response(image)
    response.headers.set("Content-Type", "image/png")
    return response, 200


@app.get("/maps/multi")
def get_maps_multiple() -> tuple[Response, int]:
    if not request.json or not request.json.get("rooms"):
        return jsonify({"message": "Please provide room codes in a json format array called 'rooms'"}), 400

    rooms = request.json.get("rooms")

    room_map: dict[tuple[str, str], list[str]] = defaultdict(list)

    for room in rooms:
        room_split = room.split("/")

        # If the room cannot be split into building and room id, then skip it
        if len(room_split) < 2:  # noqa: PLR2004
            continue

        building_id, room_id, *_ = room_split

        path = get_map_path(building_id, room_id)

        if path is not None:
            room_map[path, building_id].append(room_id)

    urls = []
    for key, rooms in room_map.items():
        urls.append(f"/maps/{key[1]}/{'|'.join(rooms)}")

    if len(urls) == 0:
        return jsonify({"message": "no rooms found in database", "urls": urls}), 404

    return jsonify({"urls": urls}), 200


def entrypoint() -> None:
    app.run(port=5004, debug=True)

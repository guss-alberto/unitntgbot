from collections import defaultdict
import uuid

from flask import Flask, Response, jsonify, make_response, request

from .renderer import get_building_name_and_floor, render_map

app = Flask(__name__)


# Get the map for a single floor in a building
@app.get("/maps/<string:building_id>")
def get_map_single(building_id: str) -> tuple[Response, int]:
    rooms = request.args.get("rooms")
    if not rooms:
        return (
            jsonify(
                {"message": "Please provide room_id codes as a comma separated list in the 'rooms' query parameter"}
            ),
            400,
        )

    rooms = rooms.upper()

    rooms = rooms.split(",")
    if len(rooms) > 20:
        return jsonify({"message": "Too many rooms were provided"}), 413  # HTTP code for payload too large

    first_room = rooms[0]
    building_name_and_floor = get_building_name_and_floor(building_id, first_room)
    if building_name_and_floor is None:
        return jsonify({"message": "Room not found or building not available"}), 404

    building_name, floor = building_name_and_floor
    image = render_map(building_name, floor, set(rooms))
    if image is None:
        return jsonify({"message": "An unknown error occured"}), 500

    response = make_response(image)
    response.headers.set("Content-Type", "image/png")
    return response, 200


# Get the map for multiple floors and buildings
@app.get("/maps/multi")
def get_maps_multiple() -> tuple[Response, int]:
    rooms = request.args.get("rooms")
    if not rooms:
        return (
            jsonify(
                {
                    "message": "Please provide building_id/room_id codes as a comma separated list in the 'rooms' query parameter"
                }
            ),
            400,
        )

    rooms = rooms.upper()

    rooms = rooms.split(",")
    if len(rooms) > 20:
        return jsonify({"message": "Too many rooms were provided"}), 413

    # Create a dictionary to map building_name and floor to a set of room_ids that are present
    # This is done because "building_id" is the id given for a site, and not for a building like
    # "povo1" and "povo2" which have the same "building_id"
    room_map: dict[tuple[str, int], set[str]] = defaultdict(set)

    for room in rooms:
        room_split = room.split("/")
        if len(room_split) != 2:  # noqa: PLR2004
            continue

        building_id, room_id = room_split
        building_name_and_floor = get_building_name_and_floor(building_id, room_id)
        if building_name_and_floor is None:
            continue

        building_name, floor = building_name_and_floor
        room_map[(building_name, floor)].add(room_id)

    if not room_map:
        return jsonify({"message": "No rooms were found"}), 404

    images = []
    for (building_name, floor), room_ids in room_map.items():
        image = render_map(building_name, floor, room_ids)
        if image is None:
            continue
        images.append(image)
        
    if not images:
        return jsonify({"message": "An unknown error occured"}), 500

    # Send the images back as a multipart response
    # Define the multipart boundary
    boundary = str(uuid.uuid4())

    # Build the multipart response body
    response_body = []
    for i, image in enumerate(images):
        response_body.append(f"--{boundary}")
        response_body.append("Content-Type: image/png")
        response_body.append(f"Content-Disposition: inline; filename=image{i}.png")
        response_body.append("")
        response_body.append(image)

    response_body.append(f"--{boundary}--")
    response_body = b"\r\n".join(part if isinstance(part, bytes) else part.encode("utf-8") for part in response_body)

    response = make_response(response_body)
    response.headers["Content-Type"] = f"multipart/mixed; boundary=\"{boundary}\""
    return response, 200


def entrypoint() -> None:
    app.run("0.0.0.0")  # noqa: S104


def develop(port: int) -> None:
    app.run(port=port, debug=True)  # noqa: S201

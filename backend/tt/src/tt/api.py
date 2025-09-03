import logging
import time
from collections import defaultdict
from datetime import datetime
from functools import wraps

import requests
from flask import Flask, Response, jsonify, make_response

from tt.stops_mapping import STOP_ID_TO_NAME

from .gtfs_fallback import gtfs_get_route

BASE_URL = "https://app-tpl.tndigit.it"
USERNAME = "mittmobile"
PASSWORD = "ecGsp.RHB3"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.181 Mobile Safari/537.36",
    "X-Requested-With": "it.tndigit.mit",
}

LOGGER = logging.getLogger(__name__)


# if we fail for more than 30 minutes, fallback
FALLBACK_DELAY = 30 * 60


def _timed_memoize(duration: int, fallback):
    def decorator(func):
        cache: dict[str, dict] = defaultdict(dict)

        @wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()

            route_id = args[0]

            # If the value is still valid return it
            if route_id in cache and current_time - cache[route_id]["timestamp"] < duration:
                return cache[route_id]["value"]

            # Otherwise update the cache
            try:
                cache[route_id]["value"] = func(*args, **kwargs)
                cache[route_id]["last_success"] = current_time
            except Exception as e:
                LOGGER.error("Error while fetching data from Trentino Trasporti: %s", e)
                if (
                    route_id not in cache
                    or "last_success" not in cache[route_id]
                    or current_time - cache[route_id]["last_success"] > FALLBACK_DELAY
                ):
                    cache[route_id]["value"] = fallback(*args, **kwargs)

            cache[route_id]["timestamp"] = current_time
            return cache[route_id]["value"]

        return wrapper

    return decorator


@_timed_memoize(32, gtfs_get_route)  # Cache lasts for 30 seconds
def get_route(route_id: str, direction_id: int) -> list:
    path = "/gtlservice/trips_new"
    # Limit has to be set to some number and cannot be left out
    response = requests.get(
        BASE_URL + path,
        params={
            "limit": 1000,
            "routeId": route_id,
            "type": "U",
            "directionId": direction_id,
        },
        auth=(USERNAME, PASSWORD),
        timeout=15,
        headers=HEADERS,
    )
    data = response.json()
    now = datetime.now().strftime("%H:%M:%S")
    data = filter(lambda x: x["stopTimes"][-1]["arrivalTime"] > now, data)
    return list(data)


app = Flask(__name__)


@app.get("/<string:route_id>/<string:sequence>")
def get_routes(route_id: str, sequence: str) -> tuple[Response, int]:
    route_data = get_route(route_id, 1)

    if len(route_data) == 0:
        return make_response(""), 204

    selected_trip = route_data[int(sequence)] if len(route_data) < int(sequence) else route_data[-1]

    stop_index = selected_trip.get("lastSequenceDetection")
    stop_index = stop_index - 1 if stop_index != 0 else None

    # Filter out useless fields and change stopId to stopName
    data = {
        "delay": selected_trip.get("delay"),
        "lastUpdate": selected_trip.get("lastEventRecivedAt"),  # Misspelled in API
        "currentStopIndex": stop_index,
        "totalRoutesCount": len(route_data),
        "stops": [
            {
                "arrivalTime": stop_time["arrivalTime"][:-3],  # Remove seconds, it's always 00 anyways
                "stopName": STOP_ID_TO_NAME.get(stop_time["stopId"], "?Unknown Stop?"),
            }
            for stop_time in selected_trip.get("stopTimes", [])
        ],
    }

    return jsonify(data), 200


def main() -> None:
    app.run("0.0.0.0")


def develop(port: int) -> None:
    app.run(port=port, debug=True)

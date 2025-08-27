import logging
from datetime import datetime
import time
from functools import wraps
from collections import defaultdict

import requests
from flask import Flask, Response, jsonify, make_response
from requests import RequestException

from tt.stops_mapping import STOP_ID_TO_NAME

BASE_URL = "https://app-tpl.tndigit.it"
USERNAME = "mittmobile"
PASSWORD = "ecGsp.RHB3"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.181 Mobile Safari/537.36",
    "X-Requested-With": "it.tndigit.mit",
}

LOGGER = logging.getLogger(__name__)

# TODO: Use cache if requests are very close to each other
# class TTCache:
#     def __init__(self) -> None:
#         self.routes = {}
#         self.stops = {}
#         self.trips = {}

#     def clear(self) -> None:
#         self.routes.clear()
#         self.stops.clear()
#         self.trips.clear()

def _timed_memoize(duration: int):
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
            except Exception as e:
                LOGGER.error("Error while fetching data from Trentino Trasporti: %s", e) 

            cache[route_id]["timestamp"] = current_time
            return cache[route_id]["value"]

        return wrapper

    return decorator


@_timed_memoize(32)  # Cache lasts for 30 seconds
def get_route(route_id: str) -> list:
    path = f"/gtlservice/trips_new"
    # Limit has to be set to some number and cannot be left out
    response = requests.get(BASE_URL + path,
            params={
                "limit": 1000,
                "routeId": route_id,
                "type": "U",
                "directionId": 1,
            },
            auth=(USERNAME, PASSWORD),
            timeout=15,
            headers=HEADERS,
        )
    data = response.json()
    now = datetime.now().strftime("%H:%M:%S")
    data = filter(lambda x: x["stopTimes"][0]["arrivalTime"] > now, data)
    return list(data)


app = Flask(__name__)


@app.get("/<string:route_id>/<string:sequence>")
def get_routes(route_id: str, sequence: str) -> tuple[Response, int]:
    data = get_route(route_id)

    if len(data) == 0:
        return make_response(""), 204

    data = data[int(sequence)]

    stop_index = data.get("lastSequenceDetection")
    stop_index = stop_index - 1 if stop_index != 0 else None

    # Filter out useless fields and change stopId to stopName
    data = {
        "delay": data.get("delay"),
        "lastUpdate": data.get("lastEventRecivedAt"),  # Misspelled in API
        "currentStopIndex": stop_index,
        "totalRoutesCount": data.get("totaleCorseInLista"),
        "stops": [
            {
                "arrivalTime": stop_time["arrivalTime"][:-3],  # Remove seconds, it's always 00 anyways
                "stopName": STOP_ID_TO_NAME.get(stop_time["stopId"], "?Unknown Stop?"),
            }
            for stop_time in data.get("stopTimes", [])
        ],
    }

    return jsonify(data), 200


def main() -> None:
    app.run("0.0.0.0")


def develop(port: int) -> None:
    app.run(port=port, debug=True)

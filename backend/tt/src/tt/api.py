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

# class ApiStop {
# 	stopId: number;
# 	stopName: string;
# 	town: string;
# 	stopCode: string;
# 	stopLat: number;
# 	stopLon: number;
# 	routes: { routeId: number }[];
# }

# class ApiRoute {
# 	routeId: number;
# 	routeShortName: string;
# 	routeLongName: string;
# 	routeColor: string | null;
# }

# class ApiTrip {
# 	tripId: string;
# 	routeId: number;
# 	oraArrivoEffettivaAFermataSelezionata: string;
# 	oraArrivoProgrammataAFermataSelezionata: string;
# 	stopNext: number | null;
# 	lastSequenceDetection: number;
# 	delay: number | null;
# 	lastEventRecivedAt: string;
# 	tripHeadsign: string;
# 	stopTimes: ApiStopTime[];
# }

# class ApiStopTime {
# 	stopId: number;
# 	stopSequence: number;
# 	arrivalTime: string;
# }

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

app = Flask(__name__)


@app.get("/<string:routeId>/<string:sequence>")
def get_routes(routeId: str, sequence: str) -> tuple[Response, int]:
    # Direction 1 is towards Piazza Dante
    path = f"/gtlservice/trips_new?limit={int(sequence) + 1}&routeId={routeId}&type=U&directionId=1"

    try:
        response = requests.get(BASE_URL + path, auth=(USERNAME, PASSWORD), timeout=10, headers=HEADERS)

    except RequestException:
        return jsonify({"message": "Trentino Trasporti data seems to be unavailable"}), 503

    # Get the last trip in the list, which is the one at index `sequence` for which data is requested
    data = response.json()

    if len(data) == 0:
        return make_response(""), 204

    data = data[-1]

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

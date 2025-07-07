import requests

from flask import Flask, Response, jsonify, make_response, request

from .stops_mapping import STOP_ID_TO_NAME

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


def entrypoint() -> None:
    app.run("0.0.0.0")


def develop(port: int) -> None:
    app.run(port=port, debug=True)


@app.get("/<routeId>/<sequence>")
def getRoutes(routeId: int, sequence: int) -> tuple[Response, int]:
    # Direction 1 is towards Piazza Dante
    path = f"/gtlservice/trips_new?limit={sequence}&routeId={routeId}&type=U&directionId=1"

    response = requests.get(BASE_URL + path, auth=(USERNAME, PASSWORD), headers=HEADERS)

    data = response.json()[-1] # Get the last trip in the list, which is the one at index `sequence` for which data is requested

    # Filter out useless fields and change stopId to stopName
    data = {
        "delay": data.get("delay"),
        "lastEventRecivedAt": data.get("lastEventRecivedAt"),
        "lastSequenceDetection": data.get("lastSequenceDetection"),
        "stops": [
            {
                "arrivalTime": stop_time["arrivalTime"],
                "stopName": STOP_ID_TO_NAME[stop_time["stopId"]],
            }
            for stop_time in data.get("stopTimes", [])
        ],
        "totaleCorseInLista": data.get("totaleCorseInLista"),
    }

    return jsonify(data), response.status_code

    # data = response.json()

    # with open("trips.json", "w") as file:
    #     file.write(response.text)

    # return data

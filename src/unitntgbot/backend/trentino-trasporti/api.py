import base64
import re

import requests

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


def _getRoutes(routeId: int, limit: int):
    path = f"/gtlservice/trips_new?limit={limit}&routeId={routeId}&type=U"

    response = requests.get(BASE_URL + path, auth=(USERNAME, PASSWORD), headers=HEADERS)

    data = response.json()

    # with open("trips.json", "w") as file:
    #     file.write(response.text)

    return data

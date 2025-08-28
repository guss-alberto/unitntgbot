from datetime import datetime

import pandas as pd

df_trips = None

# This path should contain stop_times.txt and trips.txt
# update from https://www.trentinotrasporti.it/open-data
GTFS_PATH = "backend/tt/src/tt/gtfs"


def get_df() -> pd.DataFrame:
    global df_trips
    if df_trips is None:
        df_trips = pd.read_csv(GTFS_PATH + "/stop_times.txt")
        df_routes = pd.read_csv(GTFS_PATH + "/trips.txt")[["route_id", "trip_id", "direction_id"]]

        df_trips = df_trips.join(df_routes.set_index("trip_id"), on="trip_id")

        df_trips = df_trips.rename(
            columns={
                "arrival_time": "arrivalTime",
                "stop_id": "stopId",
            },
        )

        df_trips = df_trips.sort_values("arrivalTime").sort_values("stop_sequence")
        df_trips = df_trips[["trip_id", "route_id", "arrivalTime", "stopId", "direction_id"]]

    return df_trips


def gtfs_get_route(route_id: str, direction_id: int) -> list[dict]:
    data = get_df()
    now = datetime.now().strftime("%H:%M:%S")
    data = data[(data["route_id"] == int(route_id)) & (data["direction_id"] == direction_id)]

    trips = []

    for _, group in data.groupby("trip_id"):
        if group.iloc[-1]["arrivalTime"] > now:
            trips.append(
                {
                    "lastSequenceDetection": 0,
                    "stopTimes": group[["arrivalTime", "stopId"]].to_dict("records"),
                },
            )

    return trips

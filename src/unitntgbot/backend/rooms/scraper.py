import time
from functools import wraps

import pandas as pd
import requests
from telegram.helpers import escape_markdown

from .rooms_mapping import ROOM_ID_TO_NAME


def _timed_memoize(duration: int):
    def decorator(func):
        cache: dict[str, dict] = {}

        @wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()

            building_id = args[0]

            # If the value is still valid return it
            if building_id in cache and current_time - cache[building_id]["timestamp"] < duration:
                return cache[building_id]["value"]

            cache[building_id] = {}
            # Otherwise update the cache
            cache[building_id]["value"] = func(*args, **kwargs)
            cache[building_id]["timestamp"] = current_time
            return cache[building_id]["value"]

        return wrapper

    return decorator


@_timed_memoize(60 * 30)  # Buffer lasts for 30 minutes
def get_rooms(building_id: str) -> tuple[pd.DataFrame, pd.DataFrame | None, int] | None:
    """
    Get the list of rooms available for a specific building.

    Args:
        building_id (str): The building code, for example "E0503" for Polo Ferrari.

    Returns:
        df_rooms: A Pandas dataframe contianing all rooms with respective capacity in the selected building ID
        df_events_current: A pd df containing all events currently ongoing in the building
        df_events_future: A pd df cotaining all events that haven't started yet for today in the building, used for finding when a room is next gonna be free/busy

    """
    response = requests.post(
        "https://easyacademy.unitn.it/AgendaStudentiUnitn/rooms_call.php",
        data={"sede": building_id},
        timeout=10,
    )

    data = response.json()

    # If a building_id is invalid, the response will contain an empty array for the "all_rooms" key
    if not data["all_rooms"]:
        return None

    # Get the rooms and their capacity, and filter only the things that we are interested in
    df_rooms = pd.DataFrame(data["all_rooms"]).T[["room_code", "capacity"]]
    # Map the room codes to their names, also filter out the rooms that we are not interested in
    # The rooms we are not interested in are the ones that are not in the ROOM_ID_TO_NAME dictionary
    df_rooms["name"] = df_rooms["room_code"].map(lambda x: ROOM_ID_TO_NAME.get(x, ""))
    df_rooms = df_rooms[df_rooms["name"] != ""]

    now_unix = data["file_timestamp"]
    if not data["events"]:
        return df_rooms, None, now_unix

    df_events = pd.DataFrame(data["events"])[
        ["CodiceAula", "timestamp_from", "timestamp_to", "utenti", "nome", "Annullato"]
    ].sort_values("timestamp_from")

    df_events["nome"] = df_events["nome"].map(escape_markdown)
    df_events["utenti"] = df_events["utenti"].map(escape_markdown)

    return df_rooms, df_events, now_unix

import pandas as pd
import requests

from .rooms_mapping import ROOM_ID_TO_NAME


def get_rooms(building_id: str) -> tuple[pd.DataFrame, pd.DataFrame | None, pd.DataFrame | None] | None:
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
        return df_rooms, None, None

    df_events = pd.DataFrame(data["events"])[
        ["CodiceAula", "timestamp_from", "timestamp_to", "utenti", "nome", "Annullato"]
    ]

    # Find the lectures/events that are happening right now and later in the day
    df_events_current = df_events[(df_events["timestamp_from"] < now_unix) & (df_events["timestamp_to"] > now_unix)]
    df_events_future = df_events[df_events["timestamp_from"] > now_unix]

    return df_rooms, df_events_current, df_events_future


# def entrypoint():
#     get_rooms("E0503")

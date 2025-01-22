from datetime import datetime, timedelta
from io import StringIO

import pandas as pd
import requests

API_URL = "https://opera4u.operaunitn.cloud/ajax_tools/get_week"
# The server checks for these headers, so we need to include them or the request will not work
HEADERS = {"X-Requested-With": "XMLHttpRequest", "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}

# Menu is always the same for all other canteens (except for T. Garr which has dinner too)
# IDs for canteen:
# - 1 Povo 0
# - 2 Ridotto
# - 3 Takeaway (useless)
# - 4 Pizza a Tommaso Gar (useless)
# - 5 Pizza a Povo 0 (useless)
# - 6 Mensa Povo 1
# - 7 Tommaso Garr
# - 8 Mesiano
# - 12 Mensa 24 Maggio

def _get_week_canteen_raw(date: datetime, canteen_id: int) -> list[pd.DataFrame]:
    """
    Get the list of all meals for a given week

    Args:
        date (datetime): the date to get meanu items for, will get menu for the whole week the date is in
        canteen_id (int): id of the canteen, for example Tommaso Garr is 7 and "ridotto" is 2
    Returns:
        list[pd.DataFrame]: A list containing panda DF with the HTML table raw data.
    """
    data = {"timestamp_selezionato": date.timestamp(), "tipo_menu_id": str(canteen_id)}
    response = requests.post(API_URL, headers=HEADERS, data=data, timeout=30)
    html = response.json().get("visualizzazione_settimanale").replace("<br>", "\\n")

    return pd.read_html(StringIO(html))


def get_week_meals(date: datetime) ->  list[tuple[str, bool, str]]:
    """
    Get the list of all meals for a given week

    Args:
        date (datetime): the date to get meanu items for, will get menu for the whole week the date is in
    Returns:
        list[tuple[str, bool, str]]: A list of days with menu for each, entries for both lunch and dinner.
    """
    date -= timedelta(days=date.weekday())

    lunch_df, dinner_df = _get_week_canteen_raw(date, 7)  # Get menu for Tommaso Garr
    (lesto_df,) = _get_week_canteen_raw(date, 2)  # Get menu for ridotto

    # Convert to list and ignore the header
    lunch_list = lunch_df.T.to_numpy()[1:]
    dinner_list = dinner_df.T.to_numpy()[1:]
    lesto_list = lesto_df.T.to_numpy()[1:]

    result: list[tuple[str, bool, str]] = []
    # for every day monday-friday
    for lunch, lesto, dinner in zip(lunch_list, lesto_list, dinner_list, strict=False):
        day = date.strftime("%Y-%m-%d")

        string = ""

        try:
            # Since we replace <br> with "\\n" all entries start with "\\n" too, so we have to skip it every time. this is a hack beacuse operaunitn can't have a proper API
            for item in lunch[0][2:].split("\\n"):
                r: bool = item.strip() == lesto[0][2:]  # add ®️ if it's the pick for the ridotto menu
                string += f" 🍝{'®️' if r else ' '} {item.title()}\n"

            string += "\nSecond Course:\n"
            for item in lunch[1][2:].split("\\n"):
                r: bool = item.strip() == lesto[1][2:]
                string += f" 🧆{'®️' if r else ' '} {item.title()}\n"

            string += "\nSide Dishes:\n"
            # Ridotto allows you to pick your side dish so the check is removed
            for item in lunch[2][2:].split("\\n"):
                string += f" 🥦  {item.title()}\n"
        except TypeError:
            # convert empty days to empty table rows
            string = ""
        result.append((day, False, string))

        string = ""

        try:
            # Ridotto is not available for dinner so there is no need to run the check for it
            for item in dinner[0][2:].split("\\n"):
                string += f" 🍝  {item.title()}\n"

            string += "\nSecond Course:\n"
            for item in dinner[1][2:].split("\\n"):
                string += f" 🧆  {item.title()}\n"

            string += "\nSide Dishes:\n"
            for item in dinner[2][2:].split("\\n"):
                string += f" 🥦  {item.title()}\n"

        except TypeError:
            # convert empty days to empty table rows
            string = ""

        result.append((day, True, string))
        date += timedelta(days=1)
    return result


if __name__ == "__main__":
    print(get_week_meals(datetime.today()))
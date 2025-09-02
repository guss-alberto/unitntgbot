import logging
from datetime import datetime, timedelta
from io import StringIO

import pandas as pd
import requests

logger = logging.getLogger(__name__)

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
# - 7 Tommaso Garr - also has dinner
# - 8 Mesiano
# - 12 Mensa 24 Maggio


EMOJIS = "🍝🧆🥦"
COURSE_LABELS = ["<b>First course</b>:\n", "\n<b>Second course</b>:\n", "\n<b>Side dish</b>:\n"]
FIXED_ITEMS = [["Pasta All'Olio", "Riso All'Olio"], [], []]


def _get_week_canteen_raw(date: datetime, canteen_id: int) -> list[pd.DataFrame]:
    """
    Get the list of all meals for a given week.

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


def menu_item_format(items: list[str], emoji: str, lesto: str = "") -> str:
    output = ""
    lesto = lesto.replace("\\n", "").strip()
    for item in items:
        _item = item.strip()
        r: bool = _item == lesto  # add ®️ if it's the pick for the ridotto menu
        output += f" {emoji}{'®️' if r else '<code>  </code> '}{_item.title()}\n"  # To sort of match emoji width we use 2 monospace spaces and 1 regular space

    return output


def get_week_meals(date: datetime) -> list[tuple[str, bool, str]]:
    """
    Get the list of all meals for a given week.

    Args:
        date (datetime): the date to get meanu items for, will get menu for the whole week the date is in
    Returns:
        list[tuple[str, bool, str]]: A list of days with menu for each, entries for both lunch and dinner.

    """
    date -= timedelta(days=date.weekday())

    lunch_df, dinner_df = _get_week_canteen_raw(date, 7)  # Get menu for Tommaso Garr
    (lesto_df,) = _get_week_canteen_raw(date, 2)  # Get menu for ridotto

    # Convert to list and ignore the header
    lunch_list = lunch_df.T.dropna(axis=0, how="all").to_numpy()[1:]
    dinner_list = dinner_df.T.dropna(axis=0, how="all").to_numpy()[1:]
    lesto_list = lesto_df.T.dropna(axis=0, how="all").to_numpy()[1:]

    result: list[tuple[str, bool, str]] = []

    day = date.date()
    # for every day monday-friday
    for lunch, lesto, dinner in zip(lunch_list, lesto_list, dinner_list, strict=False):
        day_str = day.strftime("%Y-%m-%d")

        output = ""

        for i, (label, emoji, fixed) in enumerate(zip(COURSE_LABELS, EMOJIS, FIXED_ITEMS, strict=True)):
            output += label

            if pd.isna(lunch[i]):
                continue

            course_ = lunch[i].split("\\n")[1:] + fixed
            # There is no side dish in pasto ridotto
            ridotto = lesto[i] if len(lesto) > i else ""
            output += menu_item_format(course_, emoji, ridotto)

        result.append((day_str, False, output))

        output = ""
        for i, (label, emoji, fixed) in enumerate(zip(COURSE_LABELS, EMOJIS, FIXED_ITEMS, strict=True)):
            output += label

            if pd.isna(dinner[i]):
                continue

            course_ = dinner[i].split("\\n")[1:] + fixed
            output += menu_item_format(course_, emoji, "")

        result.append((day_str, True, output))

        day += timedelta(days=1)
    return result


def main() -> None:
    logger.info("Weeks meals: %s", get_week_meals(datetime.today()))

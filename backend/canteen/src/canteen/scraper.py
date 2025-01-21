import sqlite3
from datetime import datetime, timedelta
from io import StringIO

import pandas as pd
import requests

API_URL = "https://opera4u.operaunitn.cloud/ajax_tools/get_week"
# The server checks for these headers, so we need to include them or the request will not work
HEADERS = {"X-Requested-With": "XMLHttpRequest", "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}

db = sqlite3.connect("db/canteen.db")


def get_week_menu(date: datetime, canteen_id: int = 7) -> list[pd.DataFrame]:
    data = {"timestamp_selezionato": date.timestamp(), "tipo_menu_id": str(canteen_id)}
    response = requests.post(API_URL, headers=HEADERS, data=data, timeout=30)
    html = response.json().get("visualizzazione_settimanale").replace("<br>", "\\n")

    return pd.read_html(StringIO(html))


def add_week_to_db(date: datetime) -> None:
    date -= timedelta(days=date.weekday())

    lunch_df, dinner_df = get_week_menu(date, 7)  # Get menu for Tommaso Garr
    (lesto_df,) = get_week_menu(date, 2)  # Get menu for ridotto

    # Convert to list and ignore the header
    lunch_list = lunch_df.T.to_numpy()[1:]
    dinner_list = dinner_df.T.to_numpy()[1:]
    lesto_list = lesto_df.T.to_numpy()[1:]

    db_rows: list[tuple[str, bool, str]] = []
    # for every day monday-friday
    for lunch, lesto, dinner in zip(lunch_list, lesto_list, dinner_list, strict=False):
        day = date.strftime("%Y-%m-%d")

        string = ""

        try:
            # Since we replace <br> with "\\n" all entries start with "\\n" too, so we have to skip it every time. this is a hack beacuse operaunitn can't have a proper API
            for item in lunch[0][2:].split("\\n"):
                r: bool = item.strip() == lesto[0][2:]  # add ®️ if it's the pick for the ridotto menu
                string += f"🍝{'®️' if r else ' '} {item.title()}\n"

            string += "\nSecond Course:\n"
            for item in lunch[1][2:].split("\\n"):
                r: bool = item.strip() == lesto[1][2:]
                string += f"🧆{'®️' if r else ' '} {item.title()}\n"

            string += "\nSide Dishes:\n"
            # Ridotto allows you to pick your side dish so the check is removed
            for item in lunch[2][2:].split("\\n"):
                string += f"🥦  {item.title()}\n"
        except TypeError:
            # convert empty days to empty table rows
            string = ""
        db_rows.append((day, False, string))

        string = ""

        try:
            # Ridotto is not available for dinner so there is no need to run the check for it
            for item in dinner[0][2:].split("\\n"):
                string += f"🍝  {item.title()}\n"

            string += "\nSecond Course:\n"
            for item in dinner[1][2:].split("\\n"):
                string += f"🧆  {item.title()}\n"

            string += "\nSide Dishes:\n"
            for item in dinner[2][2:].split("\\n"):
                string += f"🥦  {item.title()}\n"

        except TypeError:
            # convert empty days to empty table rows
            string = ""

        db_rows.append((day, True, string))
        date += timedelta(days=1)
    db.executemany("""INSERT OR REPLACE INTO Menu VALUES (?, ?, ?)""", db_rows)
    db.commit()


def get_or_update(date: datetime, dinner: bool = False) -> str:
    results = get_menu(date, dinner)
    if not results:
        add_week_to_db(date)
        results = get_menu(date, dinner)

    return "a"


def get_menu(date: datetime, dinner: bool = False) -> str | None:
    cur = db.cursor()
    cur.execute("SELECT menu FROM Menu WHERE date == ? AND is_dinner == ? LIMIT 1", (date.strftime("%Y-%m-%d"), dinner))
    results = cur.fetchall()
    if not results:
        return None
    return results[0]


if __name__ == "__main__":
    db.execute("""\
        CREATE TABLE IF NOT EXISTS Menu (
        date       TEXT                 NOT NULL,
        is_dinner  BOOLEAN              NOT NULL DEFAULT FALSE,
        menu       TEXT,
        PRIMARY KEY ( date, is_dinner )
        );""")

    get_menu(datetime.today() + timedelta(days=58))

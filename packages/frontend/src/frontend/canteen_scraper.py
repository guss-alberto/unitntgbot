import sqlite3
from datetime import datetime, timedelta

import pandas as pd
import requests

API_URL = "https://opera4u.operaunitn.cloud/ajax_tools/get_week"
# The server checks for these headers, so we need to include them or the request will not work
HEADERS = {"X-Requested-With": "XMLHttpRequest", "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}

db = sqlite3.connect("canteen.db")


def get_week_menu(date: datetime, canteen_id: int = 7) -> list[pd.DataFrame]:
    data = {"timestamp_selezionato": date.timestamp(), "tipo_menu_id": str(canteen_id)}
    response = requests.post(API_URL, headers=HEADERS, data=data, timeout=30)
    html = response.json().get("visualizzazione_settimanale").replace("<br>", "\\n")

    return pd.read_html(html)


def add_week_to_db(date: datetime) -> None:
    date -= timedelta(days=date.weekday())

    lunch_df, dinner_df = get_week_menu(date, 7)  # Get menu for Tommaso Garr
    (lesto_df,) = get_week_menu(date, 2)  # Get menu for ridotto

    # Convert to list and ignore the header
    # For some reason they don't put menus for the weekend even if Tommaso Garr is open so we skip the weekend
    lunch_list = lunch_df.T.values.tolist()[1:6]
    dinner_list = dinner_df.T.values.tolist()[1:6]
    lesto_list = lesto_df.T.values.tolist()[1:6]

    # for every day monday-friday
    for lunch, lesto, dinner in zip(lunch_list, lesto_list, dinner_list, strict=False):
        day = date.strftime("%A %Y-%m-%d")

        string = "First course:\n"
        for item in lunch[0][2:].split("\\n"):
            r: bool = item.strip() == lesto[0][2:]
            string += f"🍝{'®️' if r else ' '} {item.title()}\n"

        string += "\nSecond Course:\n"
        for item in lunch[1][2:].split("\\n"):
            r: bool = item.strip() == lesto[1][2:]
            string += f"🧆{'®️' if r else ' '} {item.title()}\n"

        string += "\nSide Dishes:\n"
        for item in lunch[2][2:].split("\\n"):
            string += f"🥦  {item.title()}\n"

        db.execute("""INSERT OR REPLACE INTO Menu VALUES (?, ?, ?)""", (day, False, string))

        string = "First course:\n"
        for item in dinner[0][2:].split("\\n"):
            string += f"🍝  {item.title()}\n"

        string += "\nSecond Course:\n"
        for item in dinner[1][2:].split("\\n"):
            string += f"🧆  {item.title()}\n"

        string += "\nSide Dishes:\n"
        for item in dinner[2][2:].split("\\n"):
            string += f"🥦  {item.title()}\n"

        db.execute("""INSERT OR REPLACE INTO Menu VALUES (?, ?, ?)""", (day, True, string))
        date += timedelta(days=1)
    db.commit()


if __name__ == "__main__":
    db.execute("""CREATE TABLE IF NOT EXISTS Menu (
        date       TEXT                 NOT NULL,
        is_dinner  BOOLEAN              NOT NULL DEFAULT FALSE,
        menu       TEXT,
        PRIMARY KEY ( date, is_dinner )
        );""")

    add_week_to_db(datetime.today())

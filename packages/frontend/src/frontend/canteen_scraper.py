import logging
import sqlite3
from datetime import datetime, timedelta

import pandas as pd
import requests

API_URL = "https://opera4u.operaunitn.cloud/ajax_tools/get_week"
# The server checks for these headers, so we need to include them or the request will not work
HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
}

db = sqlite3.connect("canteen.db")

logger = logging.getLogger(__name__)


def get_week_menu(date: datetime, canteen_id: int = 7) -> list[pd.DataFrame]:
    data = {"timestamp_selezionato": date.timestamp(), "tipo_menu_id": str(canteen_id)}
    response = requests.post(API_URL, headers=HEADERS, data=data, timeout=30)
    html = response.json().get("visualizzazione_settimanale").replace("<br>", "\\n")

    return pd.read_html(html)


def get_menu(date: datetime) -> None:  # noqa: C901
    date -= timedelta(days=date.weekday())

    lunch_df, dinner_df = get_week_menu(
        datetime.today(),
        7,
    )  # Get menu for Tommaso Garr
    (lesto_df,) = get_week_menu(datetime.today(), 2)

    # for every day of the week
    for i in range(5):
        lunch = lunch_df.iloc[:, i + 1].tolist()
        lesto = lesto_df.iloc[:, i + 1].tolist()

        day = date + timedelta(days=i)

        string = f"Menu for day {day.strftime('%A %Y-%m-%d')}: \nFirst course:\n"

        first_courses = lunch[0].split("\\n")[1:]
        first_lesto = lesto[0][2:]

        for item in first_courses:
            if item.strip() == first_lesto:
                string += f"🍝®️ {item.title()}\n"
            else:
                string += f"🍝  {item.title()}\n"

        string += "Second Course:\n"

        second_courses = lunch[1].split("\\n")[1:]
        second_lesto = lesto[1][2:]

        for item in second_courses:
            if item.strip() == second_lesto:
                string += f"🧆®️ {item.title()}\n"
            else:
                string += f"🧆  {item.title()}\n"

        string += "Side Dishes:\n"

        for item in lunch[2].split("\\n")[1:]:
            string += f"🥦  {item.title()}\n"

        logger.info(string)

    # Dinner
    for i in range(5):
        dinner = dinner_df.iloc[:, i + 1].tolist()

        day = date + timedelta(days=i)

        string = f"Dinner Menu for day {day.strftime('%A %Y-%m-%d')}: \nFirst course:\n"

        for item in dinner[0].split("\\n")[1:]:
            string += f"🍝  {item.title()}\n"

        string += "Second Course:\n"

        for item in dinner[1].split("\\n")[1:]:
            string += f"🧆  {item.title()}\n"

        string += "Side Dishes:\n"

        for item in dinner[2].split("\\n")[1:]:
            string += f"🥦  {item.title()}\n"

        logger.info(string)


if __name__ == "__main__":
    try:
        db.execute("""CREATE TABLE Menu (
            date       TEXT                 NOT NULL,
            is_dinner  BOOLEAN              NOT NULL DEFAULT FALSE,
            PRIMARY KEY ( date, is_dinner )
            );""")

    except sqlite3.OperationalError as e:
        # If the error is not that the table already exists, raise the error again
        if "already exists" not in str(e):
            raise
    menu = get_menu(datetime.today())
    logger.info(menu)

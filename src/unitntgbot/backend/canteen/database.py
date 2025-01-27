import sqlite3
from datetime import datetime, timedelta

from .scraper import get_week_meals

MAX_OFFSET_DAYS = 7 * 8  # 8 weeks
DATABASE = "db/canteen.db"

def create_table(db: sqlite3.Connection) -> None:
    db.execute(
        """\
        CREATE TABLE IF NOT EXISTS Menu (
        date       TEXT                 NOT NULL,
        is_dinner  BOOLEAN              NOT NULL DEFAULT FALSE,
        menu       TEXT,
        PRIMARY KEY ( date, is_dinner )
        );""",
    )
    db.commit()


# This function has to be run every week to keep the database up to date
def update_db(db: sqlite3.Connection, date: datetime) -> None:
    meals = get_week_meals(date)
    db.executemany("INSERT OR REPLACE INTO Menu VALUES (?, ?, ?)", meals)
    meals = get_week_meals(date + timedelta(days=MAX_OFFSET_DAYS))
    db.executemany("INSERT OR REPLACE INTO Menu VALUES (?, ?, ?)", meals)
    db.commit()


def get_menu(db: sqlite3.Connection, date: datetime, *, dinner: bool = False) -> str:
    cur = db.cursor()
    cur.execute("SELECT menu FROM Menu WHERE date == ? AND is_dinner == ? LIMIT 1", (date.strftime("%Y-%m-%d"), dinner))
    menu = cur.fetchone()
    cur.close()

    output = f"{'Dinner' if dinner else 'Lunch'} menu for {date.strftime('%A %Y-%m-%d')}\n"
    if menu and menu[0] != "":
        # Hardcode static menu items, not good practice but they don't change
        output += "\nFirst Course:\n 🍝  Riso All' Olio\n 🍝  Pasta All' Olio\n"
        output += menu[0]
        if not dinner:
            output += "\n'®️' indicates that the menu item is indicated for the 'Ridotto' menu"
    else:
        output += "\n NOT AVAILABLE"
    return output


if __name__ == "__main__":
    db = sqlite3.connect(DATABASE)
    create_table(db)
    update_db(db, datetime.today())
    print(get_menu(db, datetime.today()))

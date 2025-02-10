import sqlite3
from datetime import date, datetime

from .scraper import get_week_meals
from .settings import settings

MAX_OFFSET_DAYS = 7 * 8  # 8 weeks


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
    db.commit()


def get_menu(db: sqlite3.Connection, date: date, *, dinner: bool = False) -> str:  # TODO return None when 404
    cur = db.cursor()
    cur.execute("SELECT menu FROM Menu WHERE date == ? AND is_dinner == ? LIMIT 1", (date.strftime("%Y-%m-%d"), dinner))
    menu = cur.fetchone()
    cur.close()

    if menu:
        return menu[0]

    return "NOT AVAILABLE"


if __name__ == "__main__":
    db = sqlite3.connect(settings.DB_PATH)
    create_table(db)
    update_db(db, datetime.today())
    print(get_menu(db, datetime.today()))

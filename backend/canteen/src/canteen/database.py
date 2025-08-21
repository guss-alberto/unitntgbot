import sqlite3
from datetime import date as dtdate
from datetime import datetime

from notification_dispatcher.notification import send_notification

from canteen.scraper import get_week_meals
from canteen.settings import settings

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
    db.execute(
        """\
        CREATE TABLE IF NOT EXISTS Notifications (
           id TEXT PRIMARY KEY,
           time TEXT
        );""",
    )
    db.commit()


# This function has to be run every week to keep the database up to date
def update_db(db: sqlite3.Connection, date: datetime) -> None:
    meals = get_week_meals(date)
    db.executemany("INSERT OR REPLACE INTO Menu VALUES (?, ?, ?)", meals)
    db.commit()


def get_menu(db: sqlite3.Connection, date: dtdate, *, dinner: bool = False) -> str:  # TODO: return None when 404
    cur = db.cursor()
    cur.execute("SELECT menu FROM Menu WHERE date == ? AND is_dinner == ? LIMIT 1", (date.strftime("%Y-%m-%d"), dinner))
    menu = cur.fetchone()
    cur.close()

    if menu:
        return menu[0]

    return "NOT AVAILABLE"


def notify_users_time(db: sqlite3.Connection, time: str) -> int:
    cur = db.cursor()
    cur.execute(
        """\
        SELECT id FROM Notifications
        WHERE time = ?;
        """,
        (time),
    )

    users = cur.fetchall()
    cur.close()

    if not users:
        return 0

    menu = get_menu(db, dtdate.today())
    if menu == "NOT AVAILABLE":
        return 0

    for user_id in users:
        send_notification(user_id, menu)

    return len(users)


def set_notification_time(db: sqlite3.Connection, tg_id: str, time: str | None) -> None:
    db.execute("INSERT OR REPLACE INTO Notifications VALUES (?, ?);", (tg_id, time))
    db.commit()


if __name__ == "__main__":
    db = sqlite3.connect(settings.DB_PATH)
    create_table(db)
    update_db(db, datetime.today())
    print(get_menu(db, datetime.today()))

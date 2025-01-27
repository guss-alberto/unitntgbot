import sqlite3
from datetime import datetime, timedelta

from .scraper import UniversityLecture, get_courses_from_easyacademy, import_from_unitrentoapp

DATABASE = "db/lectures.db"


def create_tables(db: sqlite3.Connection) -> None:
    db.execute(
        """\
        CREATE TABLE IF NOT EXISTS Lectures (
            id TEXT PRIMARY KEY,
            course_id TEXT,
            course_name TEXT,
            lecturer TEXT,
            start TEXT,
            end TEXT,
            location TEXT,
            is_cancelled BOOLEAN
        );""",
    )
    db.execute(
        """\
        CREATE TABLE IF NOT EXISTS Users (
           id TEXT NOT NULL,
           course_id TEXT NOT NULL,
           PRIMARY KEY ( id, course_id )
        );""",
    )
    db.commit()


def get_lectures_for_user(db: sqlite3.Connection, user_id: str, date: datetime) -> list[UniversityLecture] | None:
    cur = db.cursor()

    # If the user doesn't have any courses selected, return None instead of empty list
    cur.execute("SELECT 1 from Users WHERE id = ? LIMIT 1;", (user_id,))
    if not cur.fetchall():
        return None

    date_str = date.strftime("%Y-%m-%d")

    cur.execute(
        """\
        SELECT Lectures.* FROM Lectures
            JOIN Users ON Users.course_id=Lectures.course_id
            WHERE lectures.start LIKE ? AND Users.id=?;
        """,
        (date_str + "%", user_id),
    )

    lectures = cur.fetchall()
    cur.close()

    return [UniversityLecture(*lecture) for lecture in lectures]


def import_for_user(db: sqlite3.Connection, user_id: str, unitnapp_url: str) -> int | None:
    courses = import_from_unitrentoapp(unitnapp_url)
    if courses is None:
        return None

    db.execute("DELETE FROM Users WHERE id=?;", (user_id,))

    db.executemany(
        "INSERT OR IGNORE INTO Users VALUES (?, ?);",
        [(user_id, course) for course in courses],
    )

    db.commit()

    return len(courses)


# This function has to be run every week or with even more frequency to keep the database up to date
# TODO: If any lecture gets modified notify users subbed to it
def update_db(db: sqlite3.Connection, date: datetime) -> None:
    cur = db.cursor()

    cur.execute("SELECT DISTINCT course_id FROM Users;")
    courses = set(cur.fetchall())
    cur.close()

    lectures = get_courses_from_easyacademy(courses, date)
    # logger.info("Found %s", len(lectures))

    db.executemany(
        "INSERT OR REPLACE INTO Lectures VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
        lectures,
    )
    db.commit()

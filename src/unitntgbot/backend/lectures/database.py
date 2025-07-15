import sqlite3
from datetime import datetime

from .scraper import UniversityLecture, get_courses_from_easyacademy, import_from_ical

tracked_courses: set[str] = set()


def _create_tables(db: sqlite3.Connection) -> None:
    db.execute(
        """\
        CREATE TABLE IF NOT EXISTS Lectures (
            id TEXT PRIMARY KEY,
            course_id TEXT,
            event_name TEXT,
            lecturer TEXT,
            start TEXT,
            end TEXT,
            room TEXT,
            is_cancelled BOOLEAN,
            last_update DATETIME DEFAULT CURRENT_TIMESTAMP
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
    db.execute(
        """\
        CREATE TABLE IF NOT EXISTS Audits (
           course_id TEXT NOT NULL,
           event_name TEXT NOT NULL,
           time TEXT NOT NULL,
           new_time TEXT,
           event CHECK(event IN ('add', 'edit', 'cancel', 'remove'))
        );""",
    )
    db.execute(
        """\
        CREATE TRIGGER IF NOT EXISTS lecture_update
        AFTER UPDATE ON Lectures
        FOR EACH ROW
        WHEN
            OLD.room != NEW.room OR
            OLD.start != NEW.start OR
            OLD.event_name != NEW.event_name
        BEGIN
            INSERT INTO Audits
            VALUES (OLD.course_id, OLD.event_name, OLD.start, NEW.start, 'edit');
        END;""",
    )

    db.execute(
        """\
        CREATE TRIGGER IF NOT EXISTS lecture_cancel
        AFTER UPDATE ON Lectures
        FOR EACH ROW
        WHEN
            OLD.is_cancelled != NEW.is_cancelled
        BEGIN
            INSERT INTO Audits
            VALUES (OLD.course_id, OLD.event_name, OLD.start, NULL, 'cancel');
        END;""",
    )

    db.execute(
        """\
        CREATE TRIGGER IF NOT EXISTS lecture_delete
        AFTER DELETE ON Lectures
        FOR EACH ROW
        BEGIN
            INSERT INTO Audits
            VALUES (OLD.course_id, OLD.event_name, OLD.start, NULL, 'remove');
        END;""",
    )

    db.execute(
        """\
        CREATE TRIGGER IF NOT EXISTS lecture_insert
        AFTER INSERT ON Lectures
        FOR EACH ROW
        BEGIN
            INSERT INTO Audits
            VALUES (NEW.course_id, NEW.event_name, NEW.start, NULL, 'insert');
        END;""",
    )
    db.commit()


def get_lectures_for_user(db: sqlite3.Connection, user_id: str, date: datetime) -> list[UniversityLecture] | None:
    cur = db.cursor()

    # If the user doesn't have any courses selected, return None instead of empty list
    cur.execute("SELECT 1 from Users WHERE id = ? LIMIT 1;", (user_id,))
    if not cur.fetchall():
        return None

    cur.execute(
        """\
        SELECT Lectures.* FROM Lectures
            JOIN Users ON Users.course_id = Lectures.course_id
            WHERE DATE(lectures.start) = DATE(?) AND Users.id = ?
            ORDER BY lectures.start;
        """,
        (date.strftime("%Y-%m-%d"), user_id),
    )

    lectures = cur.fetchall()
    cur.close()

    return [UniversityLecture(*lecture) for lecture in lectures]


def get_next_lectures_for_user(db: sqlite3.Connection, user_id: str, date: datetime) -> list[UniversityLecture]:
    cur = db.cursor()
    cur.execute(  # gets all concurrent lectures
        """\
        SELECT Lectures.* FROM Lectures
            JOIN Users ON Users.course_id = Lectures.course_id
            WHERE Lectures.start = (
                SELECT Lectures.start FROM Lectures
                JOIN Users ON Users.course_id = Lectures.course_id
                WHERE Lectures.start > ? AND Users.id = ?
                ORDER BY Lectures.start
                LIMIT 1
            )
            AND Users.id = ?;
        """,
        (date.isoformat(), user_id, user_id),
    )
    res = cur.fetchall()

    if not res:
        return []

    return [UniversityLecture(*r) for r in res]


# Adds the lectures associated with the token to the database to a user with a specific user_id, replaces the previous lectures
def import_for_user(db: sqlite3.Connection, user_id: str, token: str) -> set[str]:
    global tracked_courses
    courses = import_from_ical(token)

    db.execute("DELETE FROM Users WHERE id=?;", (user_id,))

    db.executemany(
        "INSERT OR IGNORE INTO Users VALUES (?, ?);",
        [(user_id, course) for course in courses],
    )

    if not courses.issubset(tracked_courses):
        lectures = get_courses_from_easyacademy(courses - tracked_courses, datetime.now())

        db.executemany(
            """\
            INSERT OR REPLACE INTO Lectures (id, course_id, event_name, lecturer, start, end, room, is_cancelled)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);""",
            lectures,
        )
        tracked_courses.union(courses)

    db.commit()
    return courses


# This function has to be run every week or with even more frequency to keep the database up to date
# TODO: If any lecture gets modified notify users subbed to it
def update_db(db: sqlite3.Connection, date: datetime) -> None:
    global tracked_courses
    _create_tables(db)  # Creates the tables if it does not yet exist

    cur = db.cursor()

    cur.execute("SELECT DISTINCT course_id FROM Users;")
    tracked_courses = set(cur.fetchall())

    lectures = get_courses_from_easyacademy(tracked_courses, date)
    # logger.info("Found %s", len(lectures))
    db.execute("DELETE FROM Audits;")
    db.executemany(
        """\
        INSERT INTO Lectures (id, course_id, event_name, lecturer, start, end, room, is_cancelled)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT DO
        UPDATE SET
            event_name = excluded.event_name,
            lecturer = excluded.lecturer,
            start = excluded.start,
            end = excluded.end,
            room = excluded.room,
            is_cancelled = excluded.is_cancelled,
            last_update = CURRENT_TIMESTAMP;
        """,
        lectures,
    )
    db.execute(
        """\
            DELETE FROM lectures
            WHERE last_update < datetime('now', '-1 hour')
            AND date(start) >= date('now');
        """,
    )
    cur.execute("""\
                SELECT DISTINCT Users.id, Audits.*
                FROM Audits JOIN Users ON Users.course_id = Audits.course_id
                WHERE DATE(Audits.time) < DATETIME("now", "3 weeks");
                """)
    to_notify = cur.fetchall()
    print(to_notify)
    cur.close()
    db.commit()

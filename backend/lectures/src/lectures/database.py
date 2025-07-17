import asyncio
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta

from notification_dispatcher.notification import Notification

from lectures.LectureUpdate import LectureUpdate
from lectures.scraper import get_courses_from_easyacademy, import_from_ical
from lectures.UniversityLecture import UniversityLecture

asyncio.run(Notification.start_producer())

tracked_courses: set[str] = set()
WEEKS_UPDATED = 4


def get_tracked_courses(courses: set[str], date: datetime) -> list[UniversityLecture]:
    lectures: list[UniversityLecture] = []

    for i in range(WEEKS_UPDATED):
        lectures += get_courses_from_easyacademy(courses, date + timedelta(weeks=i))

    return lectures


def create_tables(db: sqlite3.Connection) -> None:
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
        CREATE TABLE IF NOT EXISTS Changes (
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
            INSERT INTO Changes
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
            INSERT INTO Changes
            VALUES (OLD.course_id, OLD.event_name, OLD.start, NULL, 'cancel');
        END;""",
    )

    db.execute(
        """\
        CREATE TRIGGER IF NOT EXISTS lecture_delete
        AFTER DELETE ON Lectures
        FOR EACH ROW
        BEGIN
            INSERT INTO Changes
            VALUES (OLD.course_id, OLD.event_name, OLD.start, NULL, 'remove');
        END;""",
    )

    db.execute(
        """\
        CREATE TRIGGER IF NOT EXISTS lecture_insert
        AFTER INSERT ON Lectures
        FOR EACH ROW
        BEGIN
            INSERT INTO Changes
            VALUES (NEW.course_id, NEW.event_name, NEW.start, NULL, 'add');
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

    # if some lectures are not currently being tracked, add them silently without notifying users
    if not courses.issubset(tracked_courses):
        lectures = get_tracked_courses(courses - tracked_courses, datetime.now())
        db.executemany(
            """\
            INSERT OR REPLACE INTO Lectures (id, course_id, event_name, lecturer, start, end, room, is_cancelled)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);""",
            lectures,
        )
        tracked_courses = tracked_courses.union(courses)

    db.commit()
    return courses


# This function has to be run every week or with even more frequency to keep the database up to date
def update_db(db: sqlite3.Connection, date: datetime, weeks: int = 1) -> None:
    global tracked_courses
    cur = db.cursor()

    cur.execute("SELECT DISTINCT course_id FROM Users;")
    tracked_courses = set(cur.fetchall())

    lectures: list[UniversityLecture] = get_tracked_courses(tracked_courses, date)

    # logger.info("Found %s", len(lectures))
    db.execute("DELETE FROM Changes;")
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
        DELETE FROM Lectures
        WHERE last_update < datetime('now', '-1 hour')
        AND date(start) >= date('now');
        """,
    )
    cur.execute(
        """\
        SELECT DISTINCT Users.id, Changes.*
        FROM Changes JOIN Users ON Users.course_id = Changes.course_id
        WHERE DATE(Changes.time) < DATETIME("now", "3 weeks");
        """,
    )
    to_notify = cur.fetchall()
    cur.close()
    db.commit()


    # group by user
    user_changes = defaultdict(list)
    for tg_id, *u in to_notify:
        user_changes[tg_id].append(u)

    # create a single gouped notification for all the updates
    for tg_id, updates in user_changes.items():
        formatted_updates = [LectureUpdate(*u).format() for u in updates]

        message = "‼️ *LECTURE UPDATES* ‼️\n"
        message += f"{len(updates)} lectures have changed\n\n"
        message += "\n".join(formatted_updates)

        Notification(tg_id, message).send_notification()

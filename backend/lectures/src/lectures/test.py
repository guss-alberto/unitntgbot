import asyncio
import sqlite3
import time

from notification_dispatcher.notification import Notification

from lectures.database import LectureUpdate, UniversityLecture, create_tables

asyncio.run(Notification.start_producer())


async def main() -> None:
    db = sqlite3.connect("lectures_test.db")

    create_tables(db)  # Creates the tables if it does not yet exist

    cur = db.cursor()

    db.execute("INSERT OR IGNORE INTO Users VALUES (648954207, 'EC838383_Boato');")

    db.execute("DELETE FROM Lectures;")

    lectures: list[UniversityLecture] = [
        UniversityLecture(
            "123",
            "EC838383_Boato",
            "Lezione da cancellare",
            "prof",
            "2025-09-09T12:12:12",
            "2025-09-09T13:00:00",
            "A205",
            False,
        ),
        UniversityLecture(
            "124",
            "EC838383_Boato",
            "Lezione da annullare",
            "prof",
            "2025-09-09T12:12:12",
            "2025-09-09T13:00:00",
            "A205",
            False,
        ),
        UniversityLecture(
            "125",
            "EC838383_Boato",
            "Lezione da spostare",
            "prof",
            "2025-09-09T12:12:12",
            "2025-09-09T13:00:00",
            "A205",
            False,
        ),
        UniversityLecture(
            "126",
            "EC838383_Boato",
            "Lezione da modificare",
            "prof",
            "2025-09-09T12:12:12",
            "2025-09-09T13:00:00",
            "A205",
            False,
        ),
    ]

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

    db.commit()
    print("Please wait 15 seconds")
    time.sleep(5)

    lectures: list[UniversityLecture] = [
        # UniversityLecture("123", "EC838383_Boato", "Lezione da cancellare", "prof", "2025-09-09T12:12:12", "2025-09-09T13:00:00", "A205", False ),
        UniversityLecture(
            "124",
            "EC838383_Boato",
            "Lezione da annullare",
            "prof",
            "2025-09-09T12:12:12",
            "2025-09-09T13:00:00",
            "A205",
            True,
        ),
        UniversityLecture(
            "125",
            "EC838383_Boato",
            "Lezione da spostare",
            "prof",
            "2025-09-09T18:12:12",
            "2025-09-09T20:00:00",
            "A205",
            False,
        ),
        UniversityLecture(
            "126",
            "EC838383_Boato",
            "Lezione da modificare",
            "prof",
            "2025-09-09T12:12:12",
            "2025-09-09T13:00:00",
            "A208",
            False,
        ),
        UniversityLecture(
            "128",
            "EC838383_Boato",
            "Lezione NUOVA",
            "prof",
            "2025-09-09T12:12:12",
            "2025-09-09T13:00:00",
            "A208",
            False,
        ),
    ]

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
        DELETE FROM Lectures
        WHERE last_update < datetime('now', '-4 seconds')
        AND date(start) >= date('now');
        """,
    )
    cur.execute(
        """\
        SELECT DISTINCT Users.id, Audits.*
        FROM Audits JOIN Users ON Users.course_id = Audits.course_id;
        """,
    )
    to_notify = cur.fetchall()
    print(to_notify)
    cur.close()
    db.commit()

    for notification in to_notify:
        tg_id = notification[0]
        update = LectureUpdate(*notification[1:])

        await Notification(tg_id, update.format()).send_notification()
        print(f"Notification sent to {tg_id}: {update.format()}")


asyncio.run(main())

import asyncio
import sqlite3
import time
from collections import defaultdict

from notification_dispatcher.notification import Notification

from lectures.database import LectureUpdate, UniversityLecture, create_tables

# import asyncio
# import time

# from aiokafka import AIOKafkaProducer
# from notification_dispatcher.notification import Notification

# async def send() -> None:
#     await Notification.start_producer()
#     tg_id = 648954207
#     await Notification(tg_id, "__Ciao__").send_notification()
#     # await Notification.stop_producer()

# def main() -> None:
#     asyncio.run(send())


async def send_update() -> None:
    if not Notification.is_producer_started:
        await Notification.start_producer()

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
    print("Please wait 5 seconds")
    await asyncio.sleep(5)

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
        WHERE last_update < datetime('now', '-4 seconds')
        AND date(start) >= date('now');
        """,
    )
    cur.execute(
        """\
        SELECT DISTINCT Users.id, Changes.*
        FROM Changes JOIN Users ON Users.course_id = Changes.course_id;
        """,
    )
    to_notify = cur.fetchall()
    print(to_notify)
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

        await Notification(tg_id, message).send_notification()


def main() -> None:
    asyncio.run(send_update())

import logging
import re
import sqlite3
from datetime import datetime

import requests

from .UniversityLecture import UniversityLecture

def _iso_normalize_date(date: str) -> str:
    d: list[str] = date.split("-")
    return f"{d[2]:0>4}-{d[1]:0>2}-{d[0]:0>2}"


def get_courses_from_easyacademy(courses: set[str], date: datetime) -> list[UniversityLecture]:
    """
    Get the list of university lessons using the EasyAcademy API.

    Args:
        courses (set[str]): The set of courses the student is enrolled in, similar to "EC146220_MASSA", "EC145810_MARCH" or "EC145614_BOATO".
        date (datetime): the date to get lectures from, will get lectures from the whole week the date is in
    Returns:
        list[UniversityLesson]: A list of UniversityLesson objects.

    """
    lectures = []

    response = requests.post(
        "https://easyacademy.unitn.it/AgendaStudentiUnitn/grid_call.php",
        data={
            "include": "attivita",
            "visualizzazione_orario": "cal",
            "only_grid": "1",
            "anno": date.strftime("%Y"),
            "date": date.strftime("%d-%m-%Y"),
            "attivita[]": list(courses),
        },
        timeout=30,
    )
    data = response.json()

    for cella in data["celle"]:
        couse_id: str = cella["id"]
        course_id: str = cella["codice_insegnamento"]
        course_name: str = cella["nome_insegnamento"]
        lecturer: str = cella["docente"]
        is_cancelled: bool = cella["Annullato"] == "1"

        # Convert the date from "dd-mm-YYYY" to "YYYY-mm-dd", and merge it with the start and end times
        lecture_date: str = _iso_normalize_date(cella["data"])
        start: str = f"{lecture_date}T{cella['ora_inizio']}"
        end: str = f"{lecture_date}T{cella['ora_fine']}"

        room: str = cella["codice_aula"] or cella["aula"]

        lecture = UniversityLecture(
            couse_id,
            course_id,
            course_name,
            lecturer,
            start,
            end,
            room,
            is_cancelled,
        )

        lectures.append(lecture)

    return lectures


def import_from_ical(url: str) -> set[str]:
    """
    Import courses from a Unitrentoapp calendar.

    Args:
        url (str): The URL of the calendar in format https://webapi.unitn.it/unitrentoapp/profile/me/calendar/{token}.

    Returns:
        set[str]: The set of courses the student is enrolled in, similar to "EC146220_MASSA", "EC145810_MARCH" or "EC145614_BOATO".

    """
    response = requests.get(url, timeout=30)
    ical = response.text

    courses: set[str] = set()
    for course in ical.split("\nUID:"):
        match = re.match(r"^Lezione(.+)\.", course)
        if match:
            courses.add(match.group(1))

    return courses


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

    url = "https://webapi.unitn.it/unitrentoapp/profile/me/calendar/EA632CDA155A04EB25CEC0B212EED9CCBA873C781F6045799C9D7CB2BB0FC6F9"
    date = datetime.fromisoformat("2024-11-16")

    # Parse the courses
    courses = import_from_ical(url)
    logger.info("Imported courses: %s", courses)

    if courses is None:
        logger.error("Invalid URL")
        exit(1)

    lectures = get_courses_from_easyacademy(courses, date)
    logger.info("Found %s", len(lectures))

    # Put the lectures in a SQLite database
    db = sqlite3.connect("db/lectures.db")
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
    db.executemany(
        "INSERT INTO Lectures VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
        lectures,
    )
    db.commit()
    db.close()

    logger.info("Done!")

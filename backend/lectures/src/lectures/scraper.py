from dataclasses import dataclass
from datetime import datetime
import requests
import logging
import re
import sqlite3

logger = logging.getLogger(__name__)


@dataclass
class UniversityLecture:
    id: str
    course_id: str
    course_name: str
    lecturer: str
    start: str
    end: str
    location: str
    is_cancelled: bool

    def to_tuple(self) -> tuple[str, str, str, str, str, str, str, bool]:
        return (
            self.id,
            self.course_id,
            self.course_name,
            self.lecturer,
            self.start,
            self.end,
            self.location,
            self.is_cancelled,
        )

def iso_normalize_date(date: str) -> str:
    d: list[str] = [d.strip() for d in date.split("-")]
    return f"{d[2]:0>4}-{d[1]:0>2}-{d[0]:0>2}"



def get_courses_from_easyacademy(courses: set[str], date: datetime) -> list[UniversityLecture]:
    """
    Get the list of university lessons using the EasyAcademy API.

    Args:
        courses (set[str]): The set of courses the student is enrolled in, similar to "EC146220_MASSA", "EC145810_MARCH" or "EC145614_BOATO".

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
    )
    data = response.json()

    with open("tmp2.json", "w") as f:
        f.write(response.text)

    for cella in data["celle"]:
        id: str = cella["id"]
        course_id: str = cella["codice_insegnamento"]
        course_name: str = cella["nome_insegnamento"]
        lecturer: str = cella["docente"]
        is_cancelled: bool = cella["Annullato"] == "1"

        # Convert the date from "dd-mm-YYYY" to "YYYY-mm-dd", and merge it with the start and end times
        lecture_date: str = iso_normalize_date(cella["data"])
        start: str = f"{lecture_date}T{cella["ora_inizio"]}"
        end: str = f"{lecture_date}T{cella["ora_fine"]}"

        # Get the location of the lesson, there could be cases where the "codice_aula" value is empty
        # (e.g. if a lesson is at the location "Wave Lab (ex- Wireless Technologies Lab)") 
        location: str = cella["codice_aula"]
        if location:
            # This is to remove the prefix code of the site (Povo has code E0503 for example, so A110 is written as "E0503/A110")
            location = location.split("/")[-1]
        else:
            location = cella["aula"]

        lecture = UniversityLecture(
            id,
            course_id,
            course_name,
            lecturer,
            start,
            end,
            location,
            is_cancelled,
        )

        lectures.append(lecture)

    return lectures


def import_from_unitrentoapp(url: str) -> set[str]:
    """
    Import courses from a Unitrentoapp calendar.

    Args:
        url (str): The URL of the calendar in format https://webapi.unitn.it/unitrentoapp/profile/me/calendar/{token}.

    Returns:
        set[str]: The set of courses the student is enrolled in, similar to "EC146220_MASSA", "EC145810_MARCH" or "EC145614_BOATO".
    """

    courses: set[str] = set()

    # Check if the URL is valid
    if not re.match(r"^https:\/\/webapi\.unitn\.it\/unitrentoapp\/profile\/me\/calendar\/[A-F0-9]{64}$", url):
        return courses

    response = requests.get(url, timeout=30)
    ical = response.text

    for course in ical.split("\nUID:"):
        match = re.match(r"^Lezione(.+)\.", course)
        if match:
            courses.add(match.group(1))

    return courses


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    url = "https://webapi.unitn.it/unitrentoapp/profile/me/calendar/EA632CDA155A04EB25CEC0B212EED9CCBA873C781F6045799C9D7CB2BB0FC6F9"
    date = datetime.fromisoformat("2024-11-16")

    # Parse the courses
    courses = import_from_unitrentoapp(url)
    logger.info(f"Imported courses: {courses}")

    lectures = get_courses_from_easyacademy(courses, date)
    logger.info(f"Found {len(lectures)} lectures")

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
        [lecture.to_tuple() for lecture in lectures],
    )
    db.commit()
    db.close()

    logger.info("Done!")


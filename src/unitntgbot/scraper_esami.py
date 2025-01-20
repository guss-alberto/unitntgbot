import logging
import re
import sqlite3
from dataclasses import dataclass

import requests
from pyquery import PyQuery as pq  # noqa: N813

logger = logging.getLogger(__name__)

EXAMS_LIST_URL = "https://www.esse3.unitn.it/Guide/PaginaListaAppelli.do"
BASE_URL = "https://www.esse3.unitn.it/"


@dataclass
class UniversityExam:
    exam_id: str
    faculty: str
    name: str
    date: str
    registration_start: str
    registration_end: str
    partition: str
    link: str
    professors: str
    is_oral: bool
    is_partial: bool


def get_university_faculties() -> dict[int, str]:
    """
    Get the list of university departments.

    Returns:
    dict[int, str]: A dictionary where the keys are the university departments ids and the values are the department names.

    """
    faculties = {}

    response = requests.get(EXAMS_LIST_URL, timeout=30)
    html = response.text
    doc = pq(html)
    # Get the "option" elements inside the #FAC_ID select element, these contain the faculties of the university
    faculties_options = doc("#FAC_ID").find("option")

    for faculty_option in faculties_options.items():
        faculty_option_pq = pq(faculty_option)
        faculty_id = faculty_option_pq.attr("value")

        try:
            faculty_id = int(faculty_id)
        except ValueError:
            continue

        faculty_name = faculty_option_pq.text()
        faculties[faculty_id] = faculty_name

    return faculties


def get_university_exams(university_faculties: dict[int, str]) -> list[UniversityExam]:
    """
    Get the list of courses for each university department.

    Args:
    university_faculties: dict[int, str], a dictionary where the keys are the university departments ids and the values are the department names.

    Returns:
    list[UniversityExam]: A list of UniversityExam objects.

    """
    exams: list[UniversityExam] = []

    for faculty_id, faculty_name in university_faculties.items():
        response = requests.post(
            EXAMS_LIST_URL,
            data={
                "FAC_ID": faculty_id,
                "CDS_ID": "X",
                "AD_ID": "X",
                "DOCENTE_ID": "X",
                "DATA_ESA": "",
                "form_id_form1": "form1",
                "actionBar1": "Cerca",
            },
            timeout=30,
        )
        html = response.text
        doc = pq(html)
        exam_list = list(doc("#tableAppelli").find("tr").items())

        logger.info("Parsing exams for faculty %s...", faculty_name)

        for raw_exam in exam_list[2:]:
            table_items = [pq(e) for e in pq(raw_exam).find("td")]

            # This is done this way because in the exam table there could be missing values
            # in some rows, since some <td> elements can have a rowspan="2" attribute
            # this way these variables will remain the same if a row has rowspan="2"
            _number_of_registrations = table_items[-1] if len(table_items) >= 1 else _number_of_registrations  # noqa: F821
            _professors = table_items[-2] if len(table_items) >= 2 else _professors  # noqa: F821, PLR2004
            _recording = table_items[-3] if len(table_items) >= 3 else _recording  # noqa: F821, PLR2004
            _is_partial = table_items[-4] if len(table_items) >= 4 else _is_partial  # noqa: F821, PLR2004
            _is_oral = table_items[-5] if len(table_items) >= 5 else _is_oral  # noqa: F821, PLR2004
            _exam_datetime = table_items[-6] if len(table_items) >= 6 else _exam_datetime  # noqa: F821, PLR2004
            _registration_period = table_items[-7] if len(table_items) >= 7 else _registration_period  # noqa: F821, PLR2004
            _exam_session = table_items[-8] if len(table_items) >= 8 else _exam_session  # noqa: F821, PLR2004
            _id_and_name = table_items[-9] if len(table_items) >= 9 else _id_and_name  # noqa: F821, PLR2004

            # Split id and name into 2 different variables using regex
            id_and_name_regex = re.match(r"^\[(.+)\] (.+$)", _id_and_name.text())
            exam_id = id_and_name_regex.group(1)
            name = id_and_name_regex.group(2)

            # Parse dates using ISO8601
            registration_start, registration_end = parse_registration_period(_registration_period.text())

            # Shorten URL by removing unnecessary params
            exam_link = _exam_datetime.find("a").attr("href").split("&FAC_ID_SEL=")[0]
            exam_link = BASE_URL + exam_link

            # Extract date time
            exam_date, exam_time, partition = parse_exam_datetime(_exam_datetime.text())
            exam_date_full = f"{exam_date}T{exam_time}" if exam_time != "" else exam_date

            is_oral: bool = _is_oral.text() == "Orale"
            is_partial: bool = _is_partial.text() == "Prova Parziale"

            # Convert profs list into string
            professors = ", ".join(filter(lambda s: s != "", _professors.text().split("\n")))
            professors = professors.title()

            exam = UniversityExam(
                exam_id,
                faculty_name,
                name,
                exam_date_full,
                registration_start,
                registration_end,
                partition,
                exam_link,
                professors,
                is_oral,
                is_partial,
            )
            exams.append(exam)

        logger.info("Parsed exams for faculty %s!", faculty_name)

    return exams


# This function is needed because the registration period is in the format "dd/mm/yyyy - dd/mm/yyyy"
# Normally datetime would work, but it doesn't work if the year has 3 digits (it is a known Python bug: https://bugs.python.org/issue13305)
# So we have to parse the dates manually, just in case some professor decides to put a 3-digit year in the registration period
def parse_registration_period(registration_period: str) -> tuple[str, str]:
    """
    Parse the registration period.

    Args:
        registration_period: str, the registration period.

    Returns:
        str: A tuple containing the registration start and end dates.

    """
    # Extract registration start
    registration_period_regex = re.match(
        r"^([0-9]+)/([0-9]+)/([0-9]+) - ([0-9]+)/([0-9]+)/([0-9]+)",
        registration_period,
    )
    registration_start = f"{registration_period_regex.group(3)}-{registration_period_regex.group(2)}-{registration_period_regex.group(1)}"
    registration_end = f"{registration_period_regex.group(6)}-{registration_period_regex.group(5)}-{registration_period_regex.group(4)}"

    return registration_start, registration_end


def parse_exam_datetime(exam_datetime: str) -> tuple[str, str, str]:
    """
    Parse the exam date and time.

    Args:
    exam_datetime: str, the exam date and time.

    Returns:
    tuple[str, str, str]: A tuple containing the exam date, the exam time, and the partition.

    """
    # Split date from time and partition
    exam_date_regex = re.match(r"^([0-9]{2}/[0-9]{2}/[0-9]{4})(.*$)", exam_datetime)
    left_to_parse = exam_date_regex.group(2)

    # Extract date
    exam_date = re.match(r"^([0-9]+)/([0-9]+)/([0-9]+)", exam_date_regex.group(1))
    exam_date = f"{exam_date.group(3)}-{exam_date.group(2)}-{exam_date.group(1)}"

    # Extract time
    exam_time_regex = re.search(r"([0-9]{2}:[0-9]{2})", left_to_parse)
    exam_time = exam_time_regex.group(1) if exam_time_regex else ""

    # Extract partition
    # For some reason, there could be a "(A-K)" or (L-Z) at the end of the date
    # to indicate the range of students that can take the exam on that day
    exam_partition_regex = re.search(r"([A-Z]-[A-Z])", left_to_parse)
    exam_partition = exam_partition_regex.group(1) if exam_partition_regex else ""

    return exam_date, exam_time, exam_partition


# POST /Guide/PaginaListaAppelli.do HTTP/1.1
# Host: www.esse3.unitn.it
# Content-Length: 89
# Content-Type: application/x-www-form-urlencoded
# User-Agent: a

# FAC_ID=10026&CDS_ID=X&AD_ID=X&DOCENTE_ID=X&DATA_ESA=&form_id_form1=form1&actionBar1=Cerca


if __name__ == "__main__":
    # Parse the university exams
    faculties = get_university_faculties()
    exams = get_university_exams(faculties)

    # Put the exams in a SQLite database
    db = sqlite3.connect("exams.db")
    db.execute(
        """\
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER,
            faculty TEXT,
            name TEXT,
            date TEXT,
            registration_start TEXT,
            registration_end TEXT,
            partition TEXT,
            link TEXT,
            professors TEXT,
            is_oral BOOLEAN,
            is_partial BOOLEAN
        );""",
    )
    db.executemany(
        "INSERT INTO exams VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
        [
            (
                exam.id,
                exam.faculty,
                exam.name,
                exam.date,
                exam.registration_start,
                exam.registration_end,
                exam.partition,
                exam.link,
                exam.professors,
                exam.is_oral,
                exam.is_partial,
            )
            for exam in exams
        ],
    )
    db.commit()
    db.close()

    logger.info("Done!")

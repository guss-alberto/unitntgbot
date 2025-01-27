from collections import namedtuple
import logging
import re
import sqlite3

import requests
from pyquery import PyQuery as pq  # noqa: N813

logger = logging.getLogger(__name__)

EXAMS_LIST_URL = "https://www.esse3.unitn.it/Guide/PaginaListaAppelli.do"
BASE_URL = "https://www.esse3.unitn.it/"


UniversityExam = namedtuple("UniversityExam", ["exam_id", "faculty", "name", "date", "registration_start", "registration_end", "partition", "link", "professors", "is_oral", "is_partial"])


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
            faculty_id = int(str(faculty_id))
            faculty_name = str(faculty_option_pq.text())
            faculty_name = faculty_name.replace("(DIP)", "").strip()
            faculties[faculty_id] = faculty_name
        except ValueError:
            logger.info("Skipping '%s', invalid characters found", faculty_option_pq)

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
        logger.info("Fetching exams for faculty %s...", faculty_name)
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

        logger.info("Parsing...")

        html = response.text
        doc = pq(html)
        exam_list = list(doc("#tableAppelli").find("tr").items())

        # Values to cache in between cycles
        # This is done because the table sometimes has a cell wrowspanw
        cached_values: dict[str, pq] = {}
        var_names = [
            "number_of_registrations",
            "professors",
            "recording",
            "is_partial",
            "is_oral",
            "exam_datetime",
            "registration_period",
            "exam_session",
            "id_and_name",
        ]

        for raw_exam in exam_list[2:]:
            try:
                table_items = [pq(e) for e in pq(raw_exam).find("td")]

                # This is done this way because in the exam table there could be missing values
                # in some rows, since some <td> elements can have a rowspan="2" attribute
                # this way these variables will remain the same if a row has rowspan="2"
                for i, var_name in enumerate(var_names):
                    if len(table_items) > i:
                        cached_values[var_name] = table_items[-(i + 1)]

                # Split id and name into 2 different variables using regex
                id_and_name_regex = re.match(r"^\[(.+)\] (.+$)", str(cached_values["id_and_name"].text()))
                if id_and_name_regex:
                    exam_id = id_and_name_regex.group(1)
                    name = id_and_name_regex.group(2)
                else:
                    logger.error("Failed to match regex on %s", cached_values["id_and_name"])
                    continue

                # Parse dates using ISO8601
                registration_start, registration_end = _parse_registration_period(
                    str(cached_values["registration_period"].text()),
                )

                # Shorten URL by removing unnecessary params
                exam_link = cached_values["exam_datetime"].find("a").attr("href")
                exam_link = str(exam_link).split("&FAC_ID_SEL=")[0]
                exam_link = BASE_URL + exam_link

                # Extract date time
                exam_date, partition = _parse_exam_datetime(str(cached_values["exam_datetime"].text()))

                is_oral: bool = cached_values["is_oral"].text() == "Orale"
                is_partial: bool = cached_values["is_partial"].text() == "Prova Parziale"

                # Convert profs list into string
                professors = ", ".join(filter(lambda s: s != "", str(cached_values["professors"].text()).split("\n")))
                professors = professors.title()

                exam = UniversityExam(
                    exam_id,
                    faculty_name,
                    name,
                    exam_date,
                    registration_start,
                    registration_end,
                    partition,
                    exam_link,
                    professors,
                    is_oral,
                    is_partial,
                )
                exams.append(exam)
            except Exception as e:
                logger.error(e)
        logger.info("Done!")

    return exams


# Converts a date in the format D/M/Y into YYYY-MM-DD
# This function is needed because the registration period is in the format "dd/mm/yyyy - dd/mm/yyyy"
def _iso_normalize_date(date: str) -> str:
    d: list[str] = [d.strip() for d in date.split("/")]
    return f"{d[2]:0>4}-{d[1]:0>2}-{d[0]:0>2}"


# Normally datetime would work, but it doesn't work if the year has 3 digits (it is a known Python bug: https://bugs.python.org/issue13305)
# So we have to parse the dates manually, just in case some professor decides to put a 3-digit year in the registration period
def _parse_registration_period(registration_period: str) -> tuple[str, str]:
    """
    Parse the registration period.

    Args:
        registration_period: str, the registration period.

    Returns:
        str: A tuple containing the registration start and end dates.

    """
    # Extract registration start
    registration_period_split = registration_period.split(" - ")
    registration_start = _iso_normalize_date(registration_period_split[0])
    registration_end = _iso_normalize_date(registration_period_split[1])

    return registration_start, registration_end


def _parse_exam_datetime(exam_datetime: str) -> tuple[str, str]:
    """
    Parse the exam date and time.

    Args:
    exam_datetime: str, the exam date and time.

    Returns:
    tuple[str, str, str]: A tuple containing the exam date, the exam time, and the partition.

    """
    # Split date from time and partition
    (
        exam_date,
        *left_to_parse,
    ) = exam_datetime.split(" -")
    left_to_parse = " -".join(left_to_parse).strip()

    # Extract date
    exam_date = _iso_normalize_date(exam_date)

    # Extract time
    exam_time_regex = re.search(r"([0-9]{2}:[0-9]{2})", left_to_parse)
    if exam_time_regex:
        exam_date = f"{exam_date}T{exam_time_regex.group(1)}"

    # Extract partition
    # For some reason, there could be a "(A-K)" or "(L-Z)" at the end of the date
    # to indicate the range of students that can take the exam on that day
    exam_partition_regex = re.search(r"\((.*)\)$", left_to_parse)
    exam_partition = exam_partition_regex.group(1) if exam_partition_regex else ""

    return exam_date, exam_partition


# POST /Guide/PaginaListaAppelli.do HTTP/1.1
# Host: www.esse3.unitn.it
# Content-Length: 89
# Content-Type: application/x-www-form-urlencoded
# User-Agent: a

# FAC_ID=10026&CDS_ID=X&AD_ID=X&DOCENTE_ID=X&DATA_ESA=&form_id_form1=form1&actionBar1=Cerca


def entrypoint() -> None:
    logging.basicConfig(level=logging.INFO)

    # Parse the university exams
    faculties = get_university_faculties()
    exams = get_university_exams(faculties)

    # Put the exams in a SQLite database
    db = sqlite3.connect("db/exams.db")
    db.execute(
        """\
        CREATE TABLE IF NOT EXISTS Exams (
            id TEXT,
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
        exams,
    )
    db.commit()
    db.close()

    logger.info("Done!")

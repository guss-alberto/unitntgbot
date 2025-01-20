from datetime import datetime
from pyquery import PyQuery as pq
from typing import Dict, List
import re
import requests

EXAMS_LIST_URL = "https://www.esse3.unitn.it/Guide/PaginaListaAppelli.do"
BASE_URL = "https://www.esse3.unitn.it/"

class UniversityExam:
    def __init__(
        self,
        id: id,
        name: str,
        date: str,
        registration_start: str,
        registration_end: str,
        link: str,
        professors: str,
        is_oral: bool,
        is_partial: bool,
    ):
        # ID DEL CORSO, DATA, Nome del corso, Periodo Iscrizioni, Link per aula, Nomi del professori, Tipo di esame (orale, scritto), Parziale (boolean se è parziale o finale)
        self.id = id
        self.date = date
        self.name = name
        self.registration_start = registration_start
        self.registration_end = registration_end
        self.link = link
        self.professors = professors
        self.is_oral = is_oral
        self.is_partial = is_partial


def get_university_faculties() -> Dict[int, str]:
    """
    Get the list of university departments.

    Returns:
    Dict[int, str]: A dictionary where the keys are the university departments ids and the values are the department names.
    """

    global EXAMS_LIST_URL

    faculties = {}

    response = requests.get(EXAMS_LIST_URL)
    html = response.text
    doc = pq(html)
    # Get the "option" elements inside the #FAC_ID select element, these contain the faculties of the university
    faculties_options = doc("#FAC_ID").find("option")

    for faculty_option in faculties_options.items():
        faculty_option = pq(faculty_option)
        faculty_id = faculty_option.attr("value")

        try:
            faculty_id = int(faculty_id)
        except ValueError:
            continue

        faculty_name = faculty_option.text()
        faculties[faculty_id] = faculty_name

    return faculties


def get_university_exams(university_faculties: Dict[int, str]) -> List[UniversityExam]:
    """
    Get the list of courses for each university department.

    Args:
    university_faculties: Dict[int, str], a dictionary where the keys are the university departments ids and the values are the department names.

    Returns:
    List[UniversityExam]: A list of UniversityExam objects.
    """

    global EXAMS_LIST_URL, BASE_URL

    exams: List[UniversityExam] = []

    for id in university_faculties.keys():
        response = requests.post(
            EXAMS_LIST_URL,
            data={
                "FAC_ID": id,
                "CDS_ID": "X",
                "AD_ID": "X",
                "DOCENTE_ID": "X",
                "DATA_ESA": "",
                "form_id_form1": "form1",
                "actionBar1": "Cerca",
            },
        )
        html = response.text
        doc = pq(html)
        exam_list = list(doc("#tableAppelli").find("tr").items())
        print(len(exam_list))

        for exam in exam_list[2:]:
            id_and_name, _, registration_period, exam_datetime, is_oral, is_partial, _, professors, _ = [pq(e) for e in pq(exam).find("td")]

            # Split id and name into 2 different variables using regex
            id_and_name_regex = re.match(r"^\[(.+)\] (.+$)", id_and_name.text())
            id = id_and_name_regex.group(1)
            name = id_and_name_regex.group(2)
            
            # Parse dates using ISO8601
            registration_period = registration_period.text().split(" - ")
            registration_start, registration_end = [datetime.strptime(r, "%d/%m/%Y").isoformat() for r in registration_period]
            
            # Shorten URL by removing unnecessary params
            exam_link = exam_datetime.find("a").attr("href").split("&FAC_ID_SEL=")[0]
            exam_link = BASE_URL + exam_link
                
            # Extract date time
            try:
                
                # For some fucking reason, there could be a "(A-K)" or (L-Z) at the end of the date
                # to indicate the range of students that can take the exam on that day
                exam_date, exam_time = [dt.strip() for dt in exam_datetime.text()[:len("dd-mm-yyyy - HH:MM")].split("-")]
                exam_date = datetime.strptime(exam_date, "%d/%m/%Y").date().isoformat() 
                if (exam_time != ""):
                    exam_date = f"{exam_date}T{exam_time}"
            except:
                print(exam_datetime)
            is_oral: bool = is_oral.text() == "Orale"
            is_partial: bool = is_partial.text() == "Prova Parziale"
            
            # Convert profs list into string
            professors = ", ".join(filter(lambda s: s != "", professors.text().split("\n")))
            professors = professors.title()

            exam = UniversityExam(id, name, exam_date, registration_start, registration_end, exam_link, professors, is_oral, is_partial)
            exams.append(exam)

    return exams


# POST /Guide/PaginaListaAppelli.do HTTP/1.1
# Host: www.esse3.unitn.it
# Content-Length: 89
# Content-Type: application/x-www-form-urlencoded
# User-Agent: a

# FAC_ID=10026&CDS_ID=X&AD_ID=X&DOCENTE_ID=X&DATA_ESA=&form_id_form1=form1&actionBar1=Cerca


if __name__ == "__main__":
    faculties = get_university_faculties()
    exams = get_university_exams(faculties)
    print(exams)

# ID DEL CORSO, DATA, Nome del corso, Periodo Iscrizioni, Link per aula, Nomi del professori, Tipo di esame (orale, scritto), Parziale (boolean se è parziale o finale)

import sqlite3

from exams.scraper import get_university_exams, get_university_faculties
from exams.UniversityExam import UniversityExam

ITEMS_PER_PAGE = 5


def create_table(db: sqlite3.Connection) -> None:
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
    db.execute(
        """\
        CREATE TABLE IF NOT EXISTS Users (
           id TEXT NOT NULL,
           course_id TEXT NOT NULL,
           PRIMARY KEY (id, course_id)
        );""",
    )
    db.commit()


def update_db(db: sqlite3.Connection) -> None:
    # Parse the university exams
    faculties = get_university_faculties()
    exams = get_university_exams(faculties)

    # Put the exams in a SQLite database
    db.executemany(
        "INSERT INTO Exams VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
        exams,
    )
    db.commit()


def search_exams(db: sqlite3.Connection, query: str, page: int = 1) -> tuple[list[UniversityExam], int]:
    cur = db.cursor()
    cur.execute(
        """\
        SELECT COUNT(*) FROM Exams WHERE
        DATE(date) >= DATE(CURRENT_TIMESTAMP) AND
        (
            name LIKE '%' || ? || '%'
            OR professors LIKE '%' || ? || '%'
            OR id = ?
        )
        ORDER BY date;""",
        (query, query, query),
    )
    
    (total_count,) = cur.fetchone()
    
    offset = (page - 1) * ITEMS_PER_PAGE
    
    cur.execute(
        """\
        SELECT DISTINCT * FROM Exams WHERE
        DATE(date) >= DATE(CURRENT_TIMESTAMP) AND
        (
            name LIKE '%' || ? || '%'
            OR professors LIKE '%' || ? || '%'
            OR id = ?
        )
        ORDER BY date
        LIMIT ? OFFSET ?;""",
        (query, query, query, ITEMS_PER_PAGE, offset),
    )
    
    exams = [UniversityExam(*exam) for exam in cur]
    cur.close()

    return exams, total_count


def get_exams_for_user(db: sqlite3.Connection, tg_id: str, page: int = 1) -> tuple[list[UniversityExam], int]:
    cur = db.cursor()
    
    cur.execute(
        """\
        SELECT COUNT(*) FROM Exams
            JOIN Users ON Users.course_id = Exams.id
            WHERE Users.id = ?
            AND DATE(Exams.date) >= DATE(CURRENT_TIMESTAMP)
            ORDER BY Exams.date;
        """,
        (tg_id,),
    )
    
    (total_count,) = cur.fetchone()
    
    offset = (page - 1) * ITEMS_PER_PAGE
    
    cur.execute(
        """\
        SELECT Exams.* FROM Exams
            JOIN Users ON Users.course_id = Exams.id
            WHERE Users.id = ?
            AND DATE(Exams.date) >= DATE(CURRENT_TIMESTAMP)
            ORDER BY Exams.date
            LIMIT ? OFFSET ?;
        """,
        (tg_id, ITEMS_PER_PAGE, offset),
    )
    exams = [UniversityExam(*exam) for exam in cur]
    cur.close()

    return exams, total_count


def add_courses_for_user(db: sqlite3.Connection, tg_id: str, courses: list[str]) -> None:
    db.executemany("INSERT OR IGNORE INTO Users VALUES (?, ?);", [(tg_id, course) for course in courses])
    db.commit()

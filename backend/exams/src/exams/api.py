import sqlite3
from math import ceil

from flask import Flask, Response, g, jsonify, request

from exams.database import (
    add_courses_for_user,
    create_table,
    get_exams_for_user,
    update_db,
)
from exams.database import search_exams as search_exams_db, ITEMS_PER_PAGE
from exams.settings import settings
from exams.UniversityExam import UniversityExam

app = Flask(__name__)


def _get_db() -> sqlite3.Connection:
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(settings.DB_PATH)
        create_table(db)
    return db


@app.teardown_appcontext
def _close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def page_parser(res: list[UniversityExam], n_items: int, page: int) -> dict:
    n_pages = ceil(n_items / ITEMS_PER_PAGE) if n_items else 0
    page = max(1, min(page, n_pages)) if n_pages else 1

    return {
        "exams": [e._asdict() for e in res],
        "n_items": n_items,
        "n_pages": n_pages,
        "page": page,
    }


@app.post("/update/")
def update() -> tuple[Response, int]:
    update_db(_get_db())
    return Response(), 200


@app.get("/exams/search")
def get_exams() -> tuple[Response, int]:
    query = request.args.get("query")
    page = int(request.args.get("page", "0"))
    if not query:
        return jsonify({"message": "`query` parameter is missing"}), 400

    query = query.upper()
    db = _get_db()
    exams, total_count = search_exams_db(db, query)

    if not exams:
        return jsonify({"message": "No exam found with given query", "exams": []}), 404

    return jsonify(page_parser(exams, total_count, page)), 200


@app.get("/exams/user/<string:tg_id>/")
def get_exam(tg_id: str) -> tuple[Response, int]:
    db = _get_db()
    page = int(request.args.get("page", "0"))
    exams, total_count = get_exams_for_user(db, tg_id)

    if not exams:
        return jsonify({"message": "No exams found for user"}), 404

    return jsonify(page_parser(exams, total_count, page)), 200


@app.post("/exams/user/<string:tg_id>/")
def add_exam(tg_id: str) -> tuple[Response, int]:
    if not request.json or not request.json.get("courses"):
        return jsonify({"message": "Request body is missing or wrong"}), 400

    courses = request.json.get("courses")

    db = _get_db()
    add_courses_for_user(db, tg_id, courses)

    return jsonify({"message": "Added exams successfully", "count": len(courses)}), 200


def main() -> None:
    app.run("0.0.0.0")  # noqa: S104


def develop(port: int) -> None:
    app.run(port=port, debug=True)  # noqa: S201

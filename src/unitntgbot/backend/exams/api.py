import sqlite3

from flask import Flask, Response, g, jsonify, request

from .database import (
    add_courses_for_user,
    create_table,
    get_exams_for_user,
)
from .database import search_exams as search_exams_db
from .settings import settings

app = Flask(__name__)


def _get_db() -> sqlite3.Connection:
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(settings.DB_PATH)
        create_table(db)
        # update_db(db, datetime.today())  # TODO: Change this later
    return db


@app.teardown_appcontext
def _close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


# TODO: add pages system
@app.route("/exams/search")
def get_exams() -> tuple[Response, int]:
    query = request.args.get("query")

    if not query:
        return jsonify({"message": "`query` parameter is missing"}), 400

    query = query.upper()
    db = _get_db()
    exams = search_exams_db(db, query)

    if not exams:
        return jsonify({"message": "No exam found with given query", "exams": exams}), 404

    return jsonify({"exams": exams}), 200


@app.get("/exams/user/<string:tg_id>/")
def get_exam(tg_id: str) -> tuple[Response, int]:
    db = _get_db()
    exams = get_exams_for_user(db, tg_id)

    if not exams:
        return jsonify({"message": "No exams found for user"}), 404

    return jsonify({"exams": exams}), 200


@app.post("/exams/user/<string:tg_id>/")
def add_exam(tg_id: str) -> tuple[Response, int]:
    if not request.json or not request.json.get("courses"):
        return jsonify({"message": "Request body is missing or wrong"}), 400

    courses = request.json.get("courses")

    db = _get_db()
    add_courses_for_user(db, tg_id, courses)

    return jsonify({"message": "Added exams successfully", "count": len(courses)}), 200


def entrypoint() -> None:
    app.run("0.0.0.0")  # noqa: S104


def develop(port: int) -> None:
    app.run(port=port, debug=True)  # noqa: S201

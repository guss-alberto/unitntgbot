import sqlite3
from datetime import datetime, timedelta

from flask import Flask, Response, g, jsonify

from .database import DATABASE, MAX_OFFSET_DAYS, get_menu, create_table, update_db


app = Flask(__name__)


def _offset_and_format_date(date: datetime, days: int) -> str | None:
    offset_date = date + timedelta(days=days)
    delay = datetime.now() - offset_date
    if abs(delay.days) > MAX_OFFSET_DAYS:
        return None
    return offset_date.strftime("%Y-%m-%d")


def _get_db() -> sqlite3.Connection:
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        create_table(db)
        update_db(db, datetime.today())  # TODO: Change this later
    return db


@app.teardown_appcontext
def _close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


@app.route("/lunch/<string:day>")
def get_lunch(day: str) -> Response:
    try:
        date = datetime.fromisoformat(day)
        menu = get_menu(_get_db(), date)
        return jsonify(
            {
                "message": menu,
                "next": _offset_and_format_date(date, 1),
                "prev": _offset_and_format_date(date, -1),
                "nextweek": _offset_and_format_date(date, 7),
            },
        )
    except Exception as e:
        return jsonify({"message": f"Server error {e}"}, 500)


@app.route("/dinner/<string:day>")
def get_dinner(day: str) -> Response:
    try:
        date = datetime.fromisoformat(day)
        menu = get_menu(_get_db(), date, dinner=True)
        return jsonify(
            {
                "message": menu,
                "next": _offset_and_format_date(date, 1),
                "prev": _offset_and_format_date(date, -1),
                "nextweek": _offset_and_format_date(date, 7),
            },
        )
    except Exception as e:
        return jsonify({"message": f"Server error {e}"}, 500)


def entrypoint() -> None:
    app.run(port=5000, debug=True)

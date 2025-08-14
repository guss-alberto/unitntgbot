import sqlite3
import re
from datetime import datetime, timedelta

from flask import Flask, Response, g, jsonify, request

from canteen.database import create_table, get_menu, update_db, set_notification_time, notify_users_time
from canteen.settings import settings

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


@app.post("/notify/<string:time>")
def notify(time: str) -> tuple[Response, int]:
    """
    Endpoint to notify users about lectures at a specific time.
    """

    db = _get_db()
    n_users = notify_users_time(db, time)

    return jsonify({"message": f"Notifications sent to {n_users} users"}), 200


@app.post("/update/")
def update() -> tuple[Response, int]:
    update_db(_get_db(), datetime.today())
    update_db(_get_db(), datetime.today() + timedelta(days=7))
    return Response(), 200


@app.post("/<string:tg_id>/notification/<string:time>")
def set_notification(tg_id: str, time: str) -> tuple[Response, int]:
    db = _get_db()

    if not re.match(r"^\d\d:\d\d$", time):
        return jsonify({"message": "Invalid time format, expected HH:MM"}), 400

    set_notification_time(db, tg_id, time)

    return jsonify({"message": "Notification time set successfully"}), 200


@app.get("/menu/<string:lunch_or_dinner>/")
def get_menu_api(lunch_or_dinner: str) -> tuple[Response, int]:
    date = request.args.get("date")

    if lunch_or_dinner == "lunch":
        is_dinner = False
    elif lunch_or_dinner == "dinner":
        is_dinner = True
    else:
        is_dinner = None
        return jsonify({"message": "Service not found, valid services are 'lunch' and 'dinner'"}), 404

    if not date:
        date = datetime.now().date()
    else:
        try:
            date = datetime.fromisoformat(date).date()
        except ValueError:
            return jsonify({"message": "Invalid Date Format"}), 400

    db = _get_db()
    menu = get_menu(db, date, dinner=is_dinner)
    return jsonify({"menu": menu, "date": date.isoformat()}), 200


def main() -> None:
    app.run("0.0.0.0")  # noqa: S104


def develop(port: int) -> None:
    app.run(port=port, debug=True)  # noqa: S201

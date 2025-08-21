import asyncio
import json
import random
import re
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from flask import Flask, Response, g, jsonify, request
from notification_dispatcher.notification import send_notification

from lectures.database import (
    create_tables,
    get_last_lecture_users,
    get_lectures_for_user,
    get_next_lectures_for_user,
    import_for_user,
    notify_users_time,
    set_notification_time,
    update_db,
)
from lectures.settings import settings
from lectures.UniversityLecture import UniversityLecture

app = Flask(__name__)


def _get_db() -> sqlite3.Connection:
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(settings.DB_PATH)
        create_tables(db)
    return db


@app.post("/update/")
def update() -> tuple[Response, int]:
    update_db(_get_db(), datetime.today(), 10)
    return Response(), 200


@app.post("/notify/")
def notify() -> tuple[Response, int]:
    """Endpoint to notify users about lectures at a specific time."""
    time = request.args.get("time")
    if not time or not re.match(r"^\d\d:\d\d$", time):
        return jsonify({"message": "'time' parameter not present in query or malformed"}), 400

    db = _get_db()
    n_users = notify_users_time(db, time)

    return jsonify({"message": f"Notifications sent to {n_users} users"}), 200


@app.post("/last/")
def last() -> tuple[Response, int]:
    """Endpoint to get the list of users who will have their last lecture at a specific time."""
    time = request.args.get("time")
    if not time or not re.match(r"^\d\d:\d\d$", time):
        return jsonify({"message": "'time' parameter not present in query or malformed"}), 400

    db = _get_db()
    users = get_last_lecture_users(db, time)

    response = requests.get(f"{settings.TT_SVC_URL}/400/0", timeout=30)
    try:
        route = response.json()
    except json.JSONDecodeError:
        route = {}

    print(route)

    # TODO: Make formatting more elegant
    html = ""
    current_hour = datetime.now().strftime("%H:%M")
    is_next = False
    current_stop_index = route["currentStopIndex"]
    stops = route.get("stops", [])
    for idx, stop in enumerate(stops):
        arrival_time = stop["arrivalTime"]
        stop_name = stop["stopName"]

        if current_stop_index is None:
            if not is_next and current_hour <= arrival_time:
                html += f"❓ <b>{arrival_time} - {stop_name}</b>\n"
                is_next = True
            else:
                html += f"⚪ {arrival_time} - {stop_name}\n"
        elif idx == current_stop_index:
            html += f"🚌 <b>{arrival_time} - {stop_name}</b>\n"
        elif idx < current_stop_index:
            html += f"🟡 {arrival_time} - {stop_name}\n"
        else:
            html += f"🟢 {arrival_time} - {stop_name}\n"

    html += "\n"
    if route["delay"] is not None:
        delay = int(route["delay"])
        if delay == 0:
            html += "<b>Bus is on time</b>\n"
        elif delay < 0:
            html += f"<b>{-delay} minute{'s' if delay != -1 else ''} early</b>\n"
        else:
            html += f"<b>{delay} minute{'s' if delay != 1 else ''} late</b>\n"

        if delay > 37:  # very magical number
            html += random.choice(
                [
                    "Is this bus operated by Trenitalia?\n",
                    "Good luck\n",
                    "Are we sure it's not on time for the next one\n",
                    "Someone's getting fired (probably not)\n",
                    "At this point, just walk\n",
                    "Is it even moving?\n",
                    "Have you checked they aren't on strike today?\n",
                    "The wheels on the bus go round and round...\n",
                ],
            )

        current_stop = route["stops"][route["currentStopIndex"]]["stopName"]
        html += f"Currently at <i>{current_stop}</i>\n"
        html += f"<i>Last updated {datetime.fromisoformat(route['lastUpdate']).astimezone(ZoneInfo('Europe/Rome')).strftime('%H:%M')}</i>"
    else:
        html += "Real time data is not available at the moment"

    # TODO: Send notifications to users
    for chat_id in users:
        send_notification(chat_id=chat_id, message=html)

    return Response(), 200


@app.teardown_appcontext
def _close_connection(exception) -> None:
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


# POST /lectures/tgid"
# Aggiungere le lezioni associate al token al DB, e associa l'utente alle lezioni per notificarlo, e cancella tutte le iscrizioni precedenti
@app.post("/lectures/<string:tg_id>")
def add_lectures(tg_id: str) -> tuple[Response, int]:
    json = request.get_json()

    if not json:
        return jsonify({"message": "Please provide a json body"}), 400

    token = json.get("token")

    if not token:
        return jsonify({"message": "Please provide a token in json body as 'token'"}), 400

    db = _get_db()

    courses = import_for_user(db, tg_id, token)

    # Add the courses to the db of the exams service
    requests.post(
        f"{settings.EXAMS_SVC_URL}/exams/user/{tg_id}",
        json={"courses": [UniversityLecture.extract_course_id(course) for course in courses]},
        timeout=30,
    )

    return jsonify({"message": "Added lectures successfully", "number": len(courses)}), 200


# Ti dice la prossima lezione in programma per l'utente
@app.get("/lectures/<string:tg_id>/next")
def get_next_lecture(tg_id: str) -> tuple[Response, int]:
    date = datetime.now()

    db = _get_db()

    next_lectures = get_next_lectures_for_user(db, tg_id, date)

    if not next_lectures:
        return jsonify({"message": "No lecture found"}), 404

    # Checking for the any lecture is the same, just check if the first one is today
    is_today = datetime.fromisoformat(next_lectures[0].start).date() == date.date()

    return jsonify({"lectures": [lec._asdict() for lec in next_lectures], "is_today": is_today}), 200


# Prendi dal DB le lezioni associate all'utente per la data specificata, oppure per oggi se la data non è specificata
@app.get("/lectures/<string:tg_id>")
def get_lectures(tg_id: str) -> tuple[Response, int]:
    date = request.args.get("date")

    if not date:
        date = datetime.now()
    else:
        try:
            date = datetime.fromisoformat(date)
        except ValueError:
            return jsonify({"message": "Invalid Date Format"}), 400

    db = _get_db()
    lectures = get_lectures_for_user(db, tg_id, date)

    if lectures is None:
        return jsonify({"message": "User not found"}), 404

    return jsonify({"lectures": [lec._asdict() for lec in lectures]}), 200


@app.post("/<string:tg_id>/notification/")
def set_notification(tg_id: str) -> tuple[Response, int]:
    db = _get_db()

    json = request.get_json()

    if not json and not json.get("time"):
        return jsonify({"message": 'No json in body, expected "time" parameter'}), 400

    time = json.get("time")

    if time == "disable":
        set_notification_time(db, tg_id, None)
        return jsonify({"message": "Lecture notifications disabled successfully"}), 200

    if not re.match(r"^\d\d:\d\d$", time):
        return jsonify({"message": "Invalid time format, expected HH:MM"}), 400

    set_notification_time(db, tg_id, time)

    return jsonify({"message": f"Lecture notifications set successfully at {time}"}), 200


def main() -> None:
    app.run("0.0.0.0")  # noqa: S104


def develop(port: int) -> None:
    app.run(port=port, debug=True)  # noqa: S201

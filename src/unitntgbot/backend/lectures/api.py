import sqlite3
from datetime import datetime, timedelta

from flask import Flask, Response, g, jsonify, request

from .database import DATABASE, get_lectures_for_user, create_tables, update_db, import_for_user


app = Flask(__name__)


def _get_db() -> sqlite3.Connection:
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        create_tables(db)
        update_db(db, datetime.fromisoformat("2024-10-16"))  # TODO: Change this later  
        
        url = "https://webapi.unitn.it/unitrentoapp/profile/me/calendar/EA632CDA155A04EB25CEC0B212EED9CCBA873C781F6045799C9D7CB2BB0FC6F9"
        user_id = "guss"

        import_for_user(db, user_id, url)
    return db


@app.teardown_appcontext
def _close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


@app.route("/lectures/<string:tg_id>")
def get_lunch(tg_id: str) -> Response:
    date = request.args.get("date")
    
    if not date:
        date = datetime.now()
    else:
        try:
            date = datetime.fromisoformat(date)
        except ValueError:
            return jsonify({"message": "Invalid Date Format"}, 400)
    
    db = _get_db()
    lectures = get_lectures_for_user(db, tg_id, date)

    if lectures is None:
        return jsonify({"message": "No courses found"}, 404)

    return jsonify({
      "lectures": lectures
    })


def entrypoint() -> None:
    app.run(port=5001, debug=True)

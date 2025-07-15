import sqlite3
from datetime import datetime, timedelta


from flask import Flask, Response, g, jsonify, request

from .database import create_table, get_menu, update_db
from .settings import settings

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

@app.post("/update/")
def update() -> tuple[Response, int]:
    update_db(_get_db(), datetime.today()) 
    update_db(_get_db(), datetime.today()+timedelta(days=7)) 
    return Response(), 200
    

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

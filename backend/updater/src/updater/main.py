import time
from typing import NoReturn

import requests
import schedule

from updater.settings import settings


def main() -> NoReturn:
    # Update the canteen menu once a day
    CANTEEN_UPDATE_URL = f"{settings.CANTEEN_SVC_URL}/update"
    schedule.every().day.at("00:00", "Europe/Rome").do(lambda: requests.post(CANTEEN_UPDATE_URL, timeout=30))

    # Update the lectures schedule twice a day
    LECTURES_UPDATE_URL = f"{settings.LECTURES_SVC_URL}/update"
    schedule.every().day.at("08:00", "Europe/Rome").do(lambda: requests.post(LECTURES_UPDATE_URL, timeout=30))
    schedule.every().day.at("20:00", "Europe/Rome").do(lambda: requests.post(LECTURES_UPDATE_URL, timeout=30))

    # Update the exams schedule once a day
    EXAMS_UPDATE_URL = f"{settings.EXAMS_SVC_URL}/update"
    schedule.every().day.at("00:00", "Europe/Rome").do(lambda: requests.post(EXAMS_UPDATE_URL, timeout=30))

    # Notify users about lectures and canteen menu at every hour
    for hour in [
        "06:00",
        "06:30",
        "07:00",
        "07:30",
        "08:00",
        "08:30",
        "09:00",
        "09:30",
        "10:00",
        "10:30",
        "11:00",
        "11:30",
        "12:00",
        "12:30",
    ]:
        NOTIFY_LECTURES_URL = f"{settings.LECTURES_SVC_URL}/notify"
        schedule.every().day.at(hour, "Europe/Rome").do(lambda: requests.post(NOTIFY_LECTURES_URL, timeout=30, params={"time": hour}))
        NOTIFY_CANTEEN_URL = f"{settings.CANTEEN_SVC_URL}/notify"
        schedule.every().day.at(hour, "Europe/Rome").do(lambda: requests.post(NOTIFY_CANTEEN_URL, timeout=30, params={"time": hour}))

    # Notify users that will have their last lecture at a specific time
    for hour in [
        "08:30",
        "09:00",
        "09:30",
        "10:00",
        "10:30",
        "11:00",
        "11:30",
        "12:00",
        "12:30",
        "13:00",
        "13:30",
        "14:00",
        "14:30",
        "15:00",
        "15:30",
        "16:00",
        "16:30",
        "17:00",
        "17:30",
        "18:00",
        "18:30",
        "19:00",
        "19:30",
        "20:00",
        "20:30",
        "21:00",
        "21:30",
    ]:
        LAST_LECTURE_URL = f"{settings.LECTURES_SVC_URL}/last"
        def notify_last_lecture(hour: str) -> None:
            response = requests.post(LAST_LECTURE_URL, timeout=30, params={"time": hour})
            users = response.json().get("users", [])
            # TODO: Do something with the users, like sending a notification

        schedule.every().day.at(hour, "Europe/Rome").do(notify_last_lecture, hour)        

    while True:
        schedule.run_pending()
        time.sleep(60)

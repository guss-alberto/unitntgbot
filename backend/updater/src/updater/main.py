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
        NOTIFY_LECTURES_URL = f"{settings.LECTURES_SVC_URL}/notify/?time={hour}"
        schedule.every().day.at(hour, "Europe/Rome").do(lambda: requests.post(NOTIFY_LECTURES_URL, timeout=30))
        NOTIFY_CANTEEN_URL = f"{settings.CANTEEN_SVC_URL}/notify/?time={hour}"
        schedule.every().day.at(hour, "Europe/Rome").do(lambda: requests.post(NOTIFY_CANTEEN_URL, timeout=30))

    while True:
        schedule.run_pending()
        time.sleep(60)

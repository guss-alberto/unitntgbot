import time
from typing import NoReturn

import requests
import schedule

from updater.settings import settings

CANTEEN_UPDATE_URL = f"{settings.CANTEEN_SVC_URL}/update"
LECTURES_UPDATE_URL = f"{settings.LECTURES_SVC_URL}/update"
EXAMS_UPDATE_URL = f"{settings.EXAMS_SVC_URL}/update"
NOTIFY_LECTURES_URL = f"{settings.LECTURES_SVC_URL}/notify"
NOTIFY_CANTEEN_URL = f"{settings.CANTEEN_SVC_URL}/notify"
BUS_NOTIFICATION_URL = f"{settings.LECTURES_SVC_URL}/bus_notify"


def main() -> NoReturn:
    # Update the canteen menu once a day
    schedule.every().day.at("00:00", "Europe/Rome").do(lambda: requests.post(CANTEEN_UPDATE_URL, timeout=30))

    # Update the lectures schedule twice a day
    schedule.every().day.at("08:00", "Europe/Rome").do(lambda: requests.post(LECTURES_UPDATE_URL, timeout=30))
    schedule.every().day.at("20:00", "Europe/Rome").do(lambda: requests.post(LECTURES_UPDATE_URL, timeout=30))

    # Update the exams schedule once a day
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
        schedule.every().day.at(hour, "Europe/Rome").do(
            lambda hour=hour: requests.post(NOTIFY_LECTURES_URL, timeout=30, params={"time": hour}),
        )
        schedule.every().day.at(hour, "Europe/Rome").do(
            lambda hour=hour: requests.post(NOTIFY_CANTEEN_URL, timeout=30, params={"time": hour}),
        )

    while True:
        schedule.run_pending()
        time.sleep(60)

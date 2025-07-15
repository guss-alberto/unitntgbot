import requests
import schedule
import time

from unitntgbot.updater.settings import settings


def entrypoint() -> None:
    while True:
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

        while True:
            schedule.run_pending()
            time.sleep(60)

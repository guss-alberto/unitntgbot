import requests
import logging
import re

logger = logging.getLogger(__name__)


def import_from_unitnapp(url: str) -> set[str]:
    if not re.match(r"^https:\/\/webapi\.unitn\.it\/unitrentoapp\/profile\/me\/calendar\/[A-F0-9]{64}$", url):
        return set()

    response = requests.get(url, timeout=30)
    ical = response.text

    courses: set[str] = set()
    for course in ical.split("\nUID:"):
        match = re.match(r"^Lezione(.+)\.", course)
        if match:
            courses.add(match.group(1))

    return courses


if __name__ == "__main__":
    print(
        import_from_unitnapp(
            "https://webapi.unitn.it/unitrentoapp/profile/me/calendar/EA632CDA155A04EB25CEC0B212EED9CCBA873C781F6045799C9D7CB2BB0FC6F9",
        ),
    )

    logger.info("TEST")

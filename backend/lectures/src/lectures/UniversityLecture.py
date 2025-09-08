import random
import re
from datetime import datetime
from typing import NamedTuple

_BOOK_EMOJI = "📔📕📗📘📙📓📒"
_CLOCK_EMOJI = "🕛🕧🕐🕜🕑🕝🕒🕞🕓🕟🕔🕠🕕🕡🕖🕢🕗🕣🕘🕤🕙🕥🕚🕦"


def get_book(name: str) -> str:
    emoji_id = abs(hash(name)) % len(_BOOK_EMOJI)
    return _BOOK_EMOJI[emoji_id]


def get_clock(time: str) -> str:
    dtime = datetime.fromisoformat(time)
    hm = int((dtime.hour % 12) * 2 + dtime.minute / 30 + 0.5)
    return _CLOCK_EMOJI[hm]


class UniversityLecture(NamedTuple):
    id: str
    course_id: str
    event_name: str
    lecturer: str
    start: str
    end: str
    room: str
    is_cancelled: bool

    @staticmethod
    def extract_course_id(course_id: str) -> str:
        # """
        # Extracts the numeric part of the course ID. EC838383_Boato
        # A course ID is a string similar to "123456" or even "".
        # """
        exam_id_match = re.match(r"^EC(.+?)_", course_id)
        if exam_id_match:
            return exam_id_match.group(1)
        return ""

    def _get_book_emoji(self) -> str:
        return get_book(self.course_id)

    def _get_clock_emoji(self) -> str:
        return get_clock(self.start)

    def format(self) -> str:
        if not self.is_cancelled:
            return (
                f"{self._get_clock_emoji()} <code>{self.start.split('T')[1]}</code> - <code>{self.end.split('T')[1]}</code>\n"
                f"{self._get_book_emoji()} <b>{self.event_name}</b>\n"
                f"{'🧑‍🏫' if random.randint(0, 100) else '🤓'} {self.lecturer.title()}\n"
                f"📍 {self.room}"
            )

        return f"{self._get_clock_emoji()} <i>cancelled</i>\n{self._get_book_emoji()} <i>{self.event_name.title()}</i>"

import random
import re
from datetime import datetime
from typing import NamedTuple

_BOOK_EMOJI = "📔📕📗📘📙📓📒"
_CLOCK_EMOJI = "🕛🕧🕐🕜🕑🕝🕒🕞🕓🕟🕔🕠🕕🕡🕖🕢🕗🕣🕘🕤🕙🕥🕚🕦"


def get_book(name: str) -> str:
    emoji_id = abs(hash(name)) % len(_BOOK_EMOJI)
    return _BOOK_EMOJI[emoji_id]


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
        time = datetime.fromisoformat(self.start)
        hm = int((time.hour % 12) * 2 + time.minute / 30 + 0.5)
        return _CLOCK_EMOJI[hm]

    def format(self) -> str:
        if not self.is_cancelled:
            return (
                f"{self._get_clock_emoji()} • `{self.start.split('T')[1]} - {self.end.split('T')[1]}`\n"
                f"{self._get_book_emoji()} • *{self.event_name}*\n"
                f"{'🧑‍🏫' if random.randint(0, 100) else '🤓'} • {self.lecturer}\n"
                f"📍 • {self.room}"
            )

        return f"{self._get_clock_emoji()} • _cancelled_\n{self._get_book_emoji()} • _{self.event_name}_"

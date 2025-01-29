import re
import random
from datetime import datetime
from typing import NamedTuple
from hashlib import md5

from .rooms_mapping import BUILDING_ID_TO_NAME, ROOM_ID_TO_NAME

_BOOK_EMOJI = "📔📕📗📘📙📓📒"
_CLOCK_EMOJI = "🕐🕜🕑🕝🕒🕞🕓🕟🕔🕠🕕🕡🕖🕢🕗🕣🕘🕤🕙🕥🕚🕦🕛🕧"


class UniversityLecture(NamedTuple):
    id: str
    course_id: str
    course_name: str
    lecturer: str
    start: str
    end: str
    room: str
    is_cancelled: bool

    @staticmethod
    def extract_course_id(course_id: str) -> int:
        numeric_id = re.search  (r"[0-9]+", course_id)
        if numeric_id:
            return int(numeric_id.group(0))
        return 0

    @staticmethod
    def get_full_room_str(room: str) -> str:
        # There can be multiple rooms assigned for a lecture for some reason
        rooms = room.split("|")

        for i, room in enumerate(rooms):
            if "/" in room:
                building_id = room.split("/")[0]
                building_name = BUILDING_ID_TO_NAME.get(building_id, building_id)
                room_name = ROOM_ID_TO_NAME.get(room, room)
                rooms[i] = f"{building_name} - {room_name}"
            else:
                rooms[i] = ROOM_ID_TO_NAME.get(room, room)

        return " | ".join(rooms)

    def _get_book_emoji(self) -> str:
        hash_hex = md5(self.course_id.encode()).hexdigest()
        emoji_id = int(hash_hex, 16) % len(_BOOK_EMOJI)
        return _BOOK_EMOJI[emoji_id]

    def _get_clock_emoji(self) -> str:
        time = datetime.fromisoformat(self.start)
        hm = int((time.hour % 12) * 2 + time.minute / 30 + 0.5)
        return _CLOCK_EMOJI[hm]

    def format(self) -> str:
        if not self.is_cancelled:
            return (
                f"{self._get_clock_emoji()} • `{self.start.split("T")[1]} - {self.end.split("T")[1]}`\n"
                f"{self._get_book_emoji()} • *{self.course_name}*\n"
                f"{"🧑‍🏫" if random.randint(0,100) else "🤓"} • {self.lecturer}\n"
                f"📍 • {self.get_full_room_str(self.room)}"
            )

        return (
            f"{self._get_clock_emoji()} • _cancelled_\n" 
            f"{self._get_book_emoji()} • _{self.course_name}_"
        )

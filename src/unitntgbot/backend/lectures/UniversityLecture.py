import re
import random
from datetime import datetime
from typing import NamedTuple

_BOOK_EMOJI = "📔📕📗📘📙📓📒"
_CLOCK_EMOJI = "🕐🕜🕑🕝🕒🕞🕓🕟🕔🕠🕕🕡🕖🕢🕗🕣🕘🕤🕙🕥🕚🕦🕛🕧"

_BUILDING_ID_TO_NAME = {
    "ES080810283": "Povo 1",
}


class UniversityLecture(NamedTuple):
    id: str
    course_id: str
    course_name: str
    lecturer: str
    start: str
    end: str
    building_id: str
    room: str
    is_cancelled: bool

    @staticmethod
    def extract_course_id(course_id: str) -> int:
        numeric_id = re.match(r"[0-9]+", course_id)
        if numeric_id:
            return int(numeric_id.group(0))
        return 0

    @staticmethod
    def get_building_name(building_id: str) -> str:
        return _BUILDING_ID_TO_NAME.get(building_id, building_id)

    def _get_book_emoji(self) -> str:
        emoji_id = UniversityLecture.extract_course_id(self.course_id) % len(_BOOK_EMOJI)
        return _BOOK_EMOJI[emoji_id]

    def _get_clock_emoji(self) -> str:
        time = datetime.fromisoformat(self.start)
        hm = int(time.hour % 12 + time.minute / 30 + 0.5)
        return _CLOCK_EMOJI[hm]

    def format(self) -> str:
        formatted_str = f"""\
    {self._get_clock_emoji()} • {self.start.split("T")[1]} - {self.end.split("T")[1]}
    {self._get_book_emoji()} • *{self.course_name}*
    {"🧑‍🏫" if random.randint(0, 420) else "🤓"} • {self.lecturer}
    📍 • {self.room}
    """

        building = UniversityLecture.get_building_name(self.building_id)

        if building:
            return formatted_str + " - " + building + "\n"

        return formatted_str


# UniversityLecture = NamedTuple(
#     "UniversityLecture",
#     ["id", "course_id", "course_name", "lecturer", "start", "end", "building_id", "room", "is_cancelled"],
# )

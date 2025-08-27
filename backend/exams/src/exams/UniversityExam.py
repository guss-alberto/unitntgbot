import random
from typing import NamedTuple
from lectures.UniversityLecture import get_book, get_clock

_CLOCK_EMOJI = "🕛🕧🕐🕜🕑🕝🕒🕞🕓🕟🕔🕠🕕🕡🕖🕢🕗🕣🕘🕤🕙🕥🕚🕦"

class UniversityExam(NamedTuple):
    exam_id: str
    faculty: str
    name: str
    date: str
    registration_start: str
    registration_end: str
    partition: str
    link: str
    professors: str
    is_oral: bool
    is_partial: bool

    def _get_clock_emoji(self) -> str:
        return get_clock(self.date)

    def format(self) -> str:
        datetime_split = self.date.split("T")
        date = datetime_split[0]
        time = datetime_split[1] if len(datetime_split) > 1 else None

        first_line = f"{"📆" if date[-2:] == "17" else "🗓"} <b>{date}</b>"
        if time:
            first_line += f" - {self._get_clock_emoji()} <b>{time}</b>"
        if self.partition:
            first_line += f" - {self.partition}"    

        return (
            first_line + "\n"
            f'{get_book(self.exam_id)} <a href="{self.link}"><b>{self.exam_id}</b> - <b>{self.name}</b></a>\n'
            f"{'🧑‍🏫' if random.randint(0, 100) else '🤓'} <b>{self.professors}</b>\n"
        )

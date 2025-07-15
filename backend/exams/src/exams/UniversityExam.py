import random
from datetime import datetime
from typing import NamedTuple

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
        time = datetime.fromisoformat(self.date)
        hm = int((time.hour % 12) * 2 + time.minute / 30 + 0.5)
        return _CLOCK_EMOJI[hm]

    def format(self) -> str:
        datetime_split = self.date.split("T")
        date = datetime_split[0]
        time = datetime_split[1] if len(datetime_split) > 1 else None

        first_line = f"🗓 *{date}*"
        if time:
            first_line += f" - {self._get_clock_emoji()} *{time}*"
        if self.partition:
            first_line += f" - {self.partition}"

        return (
            first_line + "\n"
            f"📝 *{self.exam_id}* - *{self.name}*\n"
            f"{'🧑‍🏫' if random.randint(0, 69) else '🤓'} *{self.professors}*\n"
            f"🔗 [Link]({self.link})"
        )

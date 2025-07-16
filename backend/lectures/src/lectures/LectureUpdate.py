from datetime import datetime
from typing import NamedTuple

_BOOK_EMOJI = "📔📕📗📘📙📓📒"
_CLOCK_EMOJI = "🕛🕧🕐🕜🕑🕝🕒🕞🕓🕟🕔🕠🕕🕡🕖🕢🕗🕣🕘🕤🕙🕥🕚🕦"


class LectureUpdate(NamedTuple):
    course_id: str
    event_name: str
    time: str  # The original time of the lecture
    new_time: str | None
    event: str

    def format(self) -> str:
        msg = ""
        formatted_time = datetime.fromisoformat(self.time).strftime("%Y-%m-%d %H:%M")

        if self.event == "add":
            msg += f"➕ *NEW {self.event_name}* at _{formatted_time}_"
        elif self.event == "edit":
            msg += f"📝 CHANGED *{self.event_name}* "
            if self.new_time and self.time != self.new_time:
                formatted_new_time = datetime.fromisoformat(self.new_time).strftime("%Y-%m-%d %H:%M")
                msg += f"moved from _{formatted_time}_ to _{formatted_new_time}_"
            else:
                msg += f"at _{formatted_time}_ was modified"
        elif self.event == "cancel" or self.event == "remove":
            msg += f"❌ REMOVED *{self.event_name}* at _{formatted_time}_ was removed"

        return msg

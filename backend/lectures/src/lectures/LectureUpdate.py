from datetime import datetime
from typing import NamedTuple

from lectures.UniversityLecture import get_book


class LectureUpdate(NamedTuple):
    course_id: str
    event_name: str
    time: str  # The original time of the lecture
    new_time: str | None
    event: str

    def format(self) -> str:
        msg = ""
        formatted_time = datetime.fromisoformat(self.time).strftime("%Y\\-%m\\-%d %H:%M")
        book_emoji = get_book(self.course_id)
        match self.event:
            case "edit":
                msg += f"📝 <b>{self.event_name}{book_emoji}</b> "
                if self.new_time and self.time != self.new_time:
                    formatted_new_time = datetime.fromisoformat(self.new_time).strftime("%Y\\-%m\\-%d %H:%M")
                    msg += f"moved from <i>{formatted_time}</i> to <i>{formatted_new_time}</i>"
                else:
                    msg += f"at <i>{formatted_time}</i> was modified"
                return msg
            case "add":
                msg += f"➕ <b>NEW {self.event_name}{book_emoji}</b> at <i>{formatted_time}</i>"
            case "cancel":
                msg += f"✖️ <b>{self.event_name}{book_emoji}</b> at <i>{formatted_time}</i> was removed"
            case "remove":
                msg += f"✖️ <b>{self.event_name}{book_emoji}</b> at <i>{formatted_time}</i> was cancelled"
        return msg

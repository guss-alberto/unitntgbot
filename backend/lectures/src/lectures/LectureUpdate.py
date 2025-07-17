from datetime import datetime
from typing import NamedTuple

from UniversityLecture import get_book


class LectureUpdate(NamedTuple):
    course_id: str
    event_name: str
    time: str  # The original time of the lecture
    new_time: str | None
    event: str

    def format(self) -> str:
        msg = ""
        formatted_time = datetime.fromisoformat(self.time).strftime("%Y-%m-%d %H:%M")
        book_emoji = get_book(self.course_id)
        match self.event:
            case "edit":
                msg += f"📝 CHANGED *{self.event_name}{book_emoji}* "
                if self.new_time and self.time != self.new_time:
                    formatted_new_time = datetime.fromisoformat(self.new_time).strftime("%Y-%m-%d %H:%M")
                    msg += f"moved from _{formatted_time}_ to _{formatted_new_time}_"
                else:
                    msg += f"at _{formatted_time}_ was modified"
                return msg
            case "add":
                msg += f"➕ *NEW {self.event_name}{book_emoji}* at _{formatted_time}_"
            case "cancel":
                msg += f"❌ *{self.event_name}{book_emoji}* at _{formatted_time}_ was removed"
            case "remove":
                msg += f"✖️ *{self.event_name}{book_emoji}* at _{formatted_time}_ was cancelled"
        return msg

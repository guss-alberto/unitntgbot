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
        time = datetime.fromisoformat(self.time)
        formatted_time = time.strftime("%Y-%m-%d %H:%M")
        book_emoji = get_book(self.course_id)
        match self.event:
            case "edit":
                msg += f"✏️  <b>{book_emoji} {self.event_name}</b> "
                if self.new_time and self.time != self.new_time:
                    # show full datetime only if new day is different
                    new_time = datetime.fromisoformat(self.new_time)
                    if new_time.date() == time.date():
                        formatted_new_time = new_time.strftime("%H:%M")
                    else:
                        formatted_new_time = new_time.strftime("%Y-%m-%d %H:%M")

                    msg += f"moved from <code>{formatted_time}</code> to <code>{formatted_new_time}</code>"
                else:
                    msg += f"at <code>{formatted_time}</code> was modified"
                return msg
            case "add":
                msg += f"➕  <b>{book_emoji} <i>NEW</i> {self.event_name}</b> lecture at <code>{formatted_time}</code>"
            case "cancel":
                msg += f"✖️  <i>{book_emoji} {self.event_name}</i> at <code>{formatted_time}</code> <i>was removed</i>"
            case "remove":
                msg += f"✖️  <i>{book_emoji} {self.event_name}</i> at <code>{formatted_time}</code> <i>was cancelled</i>"
        return msg

from datetime import datetime
from typing import NamedTuple


class Room(NamedTuple):
    name: str  # The name of the room
    capacity: int  # The number of people that can fit in the room
    is_free: bool  # Whether the room is free or not in the current time
    event: str  # The name of the professor or event that is happening in the room
    time: int  # The unix timestamp when the room changes from free to busy or vice-versa

    def format(self) -> str:
        capacity = f"<i>({self.capacity})</i>" if self.capacity else ""

        time = datetime.fromtimestamp(self.time).strftime("%H:%M")

        if self.is_free:
            return f"✅<b>{self.name}</b>{capacity} Free {f'until {time}' if self.time else 'all day'}"

        # Replace with ⭕️?
        return f"🔴<b>{self.name}</b>{capacity} Busy until {time}, Now:\n{self.event.title()}"


class Event(NamedTuple):
    event: str  # The name of the professor or event that is happening in the room
    time: int  # The time when the room changes from free to busy or vice-versa
    is_free: bool  # Whether the room is free or not in the current time

    def format(self) -> str:
        time = datetime.fromtimestamp(self.time).strftime("%H:%M")

        if self.is_free:
            return f"❇️ {time if self.time else 'Now'} - Free"

        return f"🟥 {time} - {self.event.title()}"

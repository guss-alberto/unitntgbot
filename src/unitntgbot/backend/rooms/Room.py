from typing import NamedTuple


class Room(NamedTuple):
    name: str  # The name of the room
    capacity: int  # The number of people that can fit in the room
    is_free: bool  # Whether the room is free or not in the current time
    event: str  # The name of the professor or event that is happening in the room
    time: str  # The time when the room changes from free to busy or viceversa

    def format(self) -> str:
        capacity = f"_({self.capacity})_" if self.capacity else ""

        if self.is_free:
            return f"✅*{self.name}*{capacity} Free {f"until {self.time}" if self.time else "all day"}"

        # Replace with ⭕️?
        return f"🔴*{self.name}*{capacity} Busy with {self.event} until {self.time}"


class Event(NamedTuple):
    event: str  # The name of the professor or event that is happening in the room
    time: str  # The time when the room changes from free to busy or viceversa
    is_free: bool  # Whether the room is free or not in the current time

    def format(self) -> str:
        if self.is_free:
            return f"❇️ {self.time} - Free"

        return f"🟥 {self.time} - {self.event}"

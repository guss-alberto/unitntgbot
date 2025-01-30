from typing import NamedTuple


class Room(NamedTuple):
    name: str  # The name of the room
    capacity: int  # The number of people that can fit in the room
    is_free: bool  # Whether the room is free or not in the current time
    event: str  # The name of the professor or event that is happening in the room
    time: str  # The time when the room changes from free to busy or viceversa

    def format(self) -> str:
        if self.is_free:
            return f"✅*{self.name}*_({self.capacity})_ Free {f"until {self.time}" if self.time else "all day"}"

        return f"⭕️*{self.name}*_({self.capacity})_ Busy with {self.event} until {self.time}"

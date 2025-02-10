import argparse
from enum import StrEnum


class Service(StrEnum):
    BOT = "bot"
    CANTEEN = "canteen"
    EXAMS = "exams"
    LECTURES = "lectures"
    ROOMS = "rooms"
    MAPS = "maps"


def main() -> None:
    # Create the parser
    parser = argparse.ArgumentParser(description="A boilerplate script for argparse usage.")

    # Add arguments
    parser.add_argument(
        "service",
        choices=list(Service),
        help=f"Select a service from: {', '.join([service.value for service in Service])}",
    )
    # parser.add_argument("-i", "--input", type=str, help="Path to the input file.")
    # parser.add_argument("-o", "--output", type=str, help="Path to the output file.")
    # parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output.")

    args = parser.parse_args()
    service = Service(args.service)

    match service:
        case Service.BOT:
            from unitntgbot.bot import entrypoint
        case Service.CANTEEN:
            from unitntgbot.backend.canteen import entrypoint
        case Service.EXAMS:
            from unitntgbot.backend.exams import entrypoint
        case Service.LECTURES:
            from unitntgbot.backend.lectures import entrypoint
        case Service.ROOMS:
            from unitntgbot.backend.rooms import entrypoint
        case Service.MAPS:
            from unitntgbot.backend.maps import entrypoint

    entrypoint()


def develop() -> None:
    parser = argparse.ArgumentParser(description="A boilerplate script for argparse usage.")

    parser.add_argument(
        "service",
        choices=list(Service),
        help=f"Select a service from: {', '.join([service.value for service in Service])}",
    )
    parser.add_argument("--port", "-p", type=int, default=5000, help="Port to run the service on.")

    args = parser.parse_args()
    service = Service(args.service)

    match service:
        case Service.BOT:
            from unitntgbot.bot import entrypoint

            entrypoint()
            return
        case Service.CANTEEN:
            from unitntgbot.backend.canteen import develop
        case Service.EXAMS:
            from unitntgbot.backend.exams import develop
        case Service.LECTURES:
            from unitntgbot.backend.lectures import develop
        case Service.ROOMS:
            from unitntgbot.backend.rooms import develop
        case Service.MAPS:
            from unitntgbot.backend.maps import develop

    develop(args.port)

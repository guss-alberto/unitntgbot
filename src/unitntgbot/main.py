import argparse
from enum import StrEnum


class Service(StrEnum):
    BOT = "bot"
    CANTEEN = "canteen"
    EXAMS = "exams"
    LECTURES = "lectures"


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

    entrypoint()

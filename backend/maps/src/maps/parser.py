import email
import logging
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    rooms = ["E0503/A101", "E0503/A202", "E0503/A203"]
    url = f"http://127.0.0.1:5000/maps/multi?rooms={','.join(rooms)}"
    response = requests.get(url, stream=True, timeout=30)

    # Retrieve the full raw response, including headers and body
    raw_response = b"".join(f"{key}: {value}\r\n".encode() for key, value in response.headers.items())  # Headers
    raw_response += b"\r\n"  # End of headers
    raw_response += response.raw.read()  # Body

    msg = email.message_from_bytes(raw_response)

    for index, part in enumerate(msg.get_payload()):
        # Get the image bytes
        image_data: bytes = part.get_payload(decode=True)

        # Save the image as a PNG file
        with Path(f"image{index}.png").open("wb") as f:
            f.write(image_data)

        logger.info("Saved image: image%d.png", index)

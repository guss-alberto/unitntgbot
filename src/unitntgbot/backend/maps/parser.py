import email
import requests

response = requests.get("http://127.0.0.1:5000/maps/multi?rooms=E0503/A101,E0503/A202,E0503/A203", stream=True)

# Retrieve the full raw response, including headers and body
raw_response = b"".join(f"{key}: {value}\r\n".encode("utf-8") for key, value in response.headers.items())
raw_response += b"\r\n"  # End of headers
raw_response += response.raw.read() # The response body
# print(raw_response[:500])

msg = email.message_from_bytes(raw_response)
print(msg.is_multipart())

for index, part in enumerate(msg.get_payload()):
    # Check if part is of type image/png
    # Get the image bytes
    image_data = part.get_payload(decode=True)

    # Save the image as a PNG file
    with open(f"image{index}.png", "wb") as f:
        f.write(image_data)

    print(f"Saved image: image{index}.png")

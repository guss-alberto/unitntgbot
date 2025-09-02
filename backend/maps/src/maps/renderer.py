import os
import xml.etree.ElementTree as ET

import cairosvg

# Get the path of the images directory, which is the "images" directory in the same directory as this file
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(CURRENT_DIR, "images")


def render_map(building_name: str, floor: int, room_ids: set[str]) -> bytes | None:
    """
    Render the svg only showing selected rooms.

    Args:
        building_name (str): The name of the building.
        floor (int): The floor number, ground floor is 0.
        room_ids (set[str]): The room ids to highlight.

    Returns:
        bytes: The rendered image in png format.

    """
    filepath = os.path.join(IMAGES_DIR, f"{building_name}-floor{floor}.svg")

    if filepath is None:
        return None

    with open(filepath, encoding="utf-8") as f:
        svg_content = f.read()

    # Load SVG file
    root = ET.fromstring(svg_content)

    # Find elements with a specific ID
    namespace = {"svg": "http://www.w3.org/2000/svg"}
    for element in root.findall(".//*[@id]", namespace):
        if element.get("id") in room_ids:
            element.set("fill", "#CE0E2D")

    # Edge case for T1A and T1B rooms in mesiano - floor 0
    # If any of those 2 rooms appear then make T1 hidden, and make T1A and T1B visible
    if building_name == "mesiano" and floor == 0 and ("T1/A" in room_ids or "T1/B" in room_ids):
        for element in root.findall(".//*[@id]", namespace):
            if element.get("id") == "T1":
                element.set("visibility", "hidden")
            elif element.get("id") in {"T1A", "T1B"}:
                element.set("visibility", "visible")

    # Save modified SVG
    modified_svg = ET.tostring(root, encoding="utf-8")

    # Convert modified SVG to PNG
    return cairosvg.svg2png(bytestring=modified_svg)


def get_building_name_and_floor(building_id: str, room_id: str) -> tuple[str, int] | None:
    """
    Get the building name and floor of a room in a specific site.

    Args:
        building_id (str): The building id.
        room_id (str): The room id.

    Returns:
        int: The floor number.

    """
    floor = None
    building_name = None

    match building_id:
        case "E0503":  # Povo
            if room_id.startswith("A1"):
                building_name = "povo1"
                floor = 0
            elif room_id.startswith("A2"):
                building_name = "povo1"
                floor = 1
            elif room_id.startswith("B1"):
                building_name = "povo2"
                floor = 0
        case "E0301":  # Mesiano
            if room_id.startswith("T"):
                building_name = "mesiano"
                floor = 0
            elif room_id.startswith("1"):
                building_name = "mesiano"
                floor = 1
            elif room_id.startswith("2"):
                building_name = "mesiano"
                floor = 2
            elif room_id.startswith("3"):
                building_name = "mesiano"
                floor = 3
            elif room_id.startswith("4"):
                building_name = "mesiano"
                floor = 4

    if building_name is None or floor is None:
        return None

    return building_name, floor


if __name__ == "__main__":
    png = render_map("povo1", 1, {"A201"})

    if png is None:
        print("An error occurred while rendering the image.")
        exit(1)

    # Save the image
    with open("images/povo1-floor0.png", "wb") as f:
        f.write(png)

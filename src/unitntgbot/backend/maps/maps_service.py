import xml.etree.ElementTree as ET

import cairosvg


def render_room_map(svg: str, rooms: list[str]) -> bytes | None:
    """
    Render the svg only showing selected rooms.

    Args:
        svg (str): the raw svg data, this has to be an Inkscape SVG file, where the inkscape:label (easily set in the "Layers and Objects" tab)
                   of certain objects is set to the name of the room prepended by a ":", example:
                       <path
                        style= -..
                        d= ...
                        id= ..
                        inkscape:label=":A110" />
                   the ":" is used to only remove unselected rooms and objects that have to always be rendered, if named, must not have a ":" in the first position of the label
        rooms (list[str]): A list of room names to be displayed

    Returns:
        bytes: raw png data of the rendered SVG

    """
    root = ET.ElementTree(ET.fromstring(svg)).getroot()  # noqa: S314

    namespaces = {"inkscape": "http://www.inkscape.org/namespaces/inkscape"}

    for parent in root.findall(".//{http://www.w3.org/2000/svg}*"):
        for path in list(parent):
            label = path.attrib.get(f"{{{namespaces["inkscape"]}}}label")
            # ignore if no label has been set
            # also ignore if the label doesn't start with ":" for the reason stated in doctrsing
            if not label or label[0] != ":":
                continue
            if label[1:] not in rooms:
                parent.remove(path)

    # Convert back to raw svg string
    modified_svg = ET.tostring(root, encoding="utf-8", method="xml")

    # Render to PNG
    return cairosvg.svg2png(modified_svg)


if __name__ == "__main__":
    with open("src/unitntgbot/backend/rooms_map/maps/map.svg") as f:
        svg_raw = f.read()
    png = render_room_map(svg_raw, ["A101", "A104"])

    with open("output.png", "wb") as f:
        if png:
            f.write(png)


#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime
import hashlib
import shutil
import textwrap
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw, ImageFont


HOME = Path.home()

SYSTEMS = (
    "xbox",
    "ps3",
    "switch",
)

FONT_PATH = (
    HOME
    / ".emulationstation"
    / "themes"
    / "carbon-custom"
    / "art"
    / "Cabin-Bold.ttf"
)

WIDTH = 1000
HEIGHT = 300


def split_title(title: str) -> list[str]:
    title = " ".join(title.upper().split())

    if len(title) <= 22:
        return [title]

    lines = textwrap.wrap(
        title,
        width=22,
        break_long_words=False,
        break_on_hyphens=False,
    )

    return lines[:2]


def choose_font_size(lines: list[str]) -> int:
    longest = max(len(line) for line in lines)

    if longest <= 14:
        return 88

    if longest <= 20:
        return 72

    if longest <= 27:
        return 58

    return 48


def create_marquee(
    title: str,
    destination: Path,
) -> None:
    lines = split_title(title)
    font_size = choose_font_size(lines)

    font = ImageFont.truetype(
        str(FONT_PATH),
        font_size,
    )

    image = Image.new(
        "RGBA",
        (WIDTH, HEIGHT),
        (0, 0, 0, 0),
    )

    draw = ImageDraw.Draw(image)

    spacing = 18

    boxes = [
        draw.textbbox(
            (0, 0),
            line,
            font=font,
            stroke_width=3,
        )
        for line in lines
    ]

    heights = [
        bottom - top
        for left, top, right, bottom in boxes
    ]

    total_height = sum(heights)

    if len(lines) > 1:
        total_height += spacing

    y = (HEIGHT - total_height) // 2

    for line, box, line_height in zip(
        lines,
        boxes,
        heights,
    ):
        left, top, right, bottom = box
        line_width = right - left

        x = (WIDTH - line_width) // 2

        # Halo rouge sombre
        draw.text(
            (x, y - top),
            line,
            font=font,
            fill=(216, 216, 216, 255),
            stroke_width=7,
            stroke_fill=(80, 0, 0, 110),
        )

        # Contour Carbon rouge
        draw.text(
            (x, y - top),
            line,
            font=font,
            fill=(216, 216, 216, 255),
            stroke_width=3,
            stroke_fill=(139, 0, 0, 255),
        )

        y += line_height + spacing

    image.save(destination)


def process_system(system: str) -> None:
    gamelist = (
        HOME
        / ".emulationstation"
        / "gamelists"
        / system
        / "gamelist.xml"
    )

    output_dir = (
        HOME
        / ".emulationstation"
        / "downloaded_media"
        / system
        / "marquees"
    )

    if not gamelist.is_file():
        print(f"⚠️ {system}: gamelist absent, ignoré")
        return

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    stamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )

    backup = gamelist.with_name(
        f"gamelist.xml.bak-marquee-png-{stamp}"
    )

    shutil.copy2(
        gamelist,
        backup,
    )

    tree = ET.parse(gamelist)
    root = tree.getroot()

    count = 0

    for game in root.findall("game"):
        name_node = game.find("name")

        if name_node is None or not name_node.text:
            continue

        title = name_node.text.strip()

        digest = hashlib.sha1(
            title.encode("utf-8")
        ).hexdigest()[:12]

        marquee_path = (
            output_dir
            / f"{digest}.png"
        )

        create_marquee(
            title,
            marquee_path,
        )

        marquee_node = game.find("marquee")

        if marquee_node is None:
            marquee_node = ET.SubElement(
                game,
                "marquee",
            )

        marquee_node.text = str(
            marquee_path
        )

        count += 1

    try:
        ET.indent(
            tree,
            space="  ",
        )
    except AttributeError:
        pass

    temporary = gamelist.with_name(
        "gamelist.xml.tmp"
    )

    tree.write(
        temporary,
        encoding="utf-8",
        xml_declaration=True,
    )

    ET.parse(temporary)
    temporary.replace(gamelist)

    print(f"✅ {system}: {count} bandeaux générés")
    print(f"   Sauvegarde : {backup}")


if not FONT_PATH.is_file():
    raise SystemExit(
        f"Police introuvable : {FONT_PATH}"
    )

for system_name in SYSTEMS:
    process_system(system_name)

print()
print("🎮 Xbox, PS3 et Switch terminées.")

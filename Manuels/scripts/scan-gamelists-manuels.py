#!/usr/bin/env python3

from pathlib import Path
import xml.etree.ElementTree as ET
import csv
import re

HOME = Path.home()

GAMELISTS_DIR = HOME / ".emulationstation" / "gamelists"
MANUALS_DIR = HOME / "RetroPie" / "manuals"

OUTPUT_CSV = HOME / "liste-jeux-pour-manuels.csv"


def clean_filename(name: str) -> str:
    name = name.strip()

    replacements = {
        ":": " -",
        "/": "-",
        "\\": "-",
        "?": "",
        "*": "",
        '"': "",
        "<": "",
        ">": "",
        "|": "-",
    }

    for old, new in replacements.items():
        name = name.replace(old, new)

    name = re.sub(r"\s+", " ", name)
    return name.strip()


def read_games_from_gamelist(gamelist_path: Path):
    system = gamelist_path.parent.name

    try:
        tree = ET.parse(gamelist_path)
    except ET.ParseError as error:
        print(f"❌ XML invalide : {gamelist_path}")
        print(f"   {error}")
        return []

    root = tree.getroot()
    games = []

    for game in root.findall("game"):
        name_node = game.find("name")
        path_node = game.find("path")
        manual_node = game.find("manual")

        if name_node is None or not name_node.text:
            continue

        name = name_node.text.strip()
        rom_path = path_node.text.strip() if path_node is not None and path_node.text else ""

        manual_name = clean_filename(name) + ".pdf"
        manual_path = MANUALS_DIR / system / manual_name

        games.append({
            "system": system,
            "name": name,
            "rom_path": rom_path,
            "manual_present_in_gamelist": manual_node.text.strip() if manual_node is not None and manual_node.text else "",
            "suggested_manual_path": str(manual_path),
            "manual_exists": manual_path.is_file(),
        })

    return games


def main():
    if not GAMELISTS_DIR.is_dir():
        raise SystemExit(f"Dossier introuvable : {GAMELISTS_DIR}")

    all_games = []

    for gamelist_path in sorted(GAMELISTS_DIR.glob("*/gamelist.xml")):
        games = read_games_from_gamelist(gamelist_path)
        all_games.extend(games)

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "system",
                "name",
                "rom_path",
                "manual_present_in_gamelist",
                "suggested_manual_path",
                "manual_exists",
            ],
        )

        writer.writeheader()
        writer.writerows(all_games)

    print(f"✅ Jeux trouvés : {len(all_games)}")
    print(f"📄 CSV généré : {OUTPUT_CSV}")

    systems = sorted(set(game["system"] for game in all_games))

    print()
    print("Systèmes détectés :")
    for system in systems:
        count = sum(1 for game in all_games if game["system"] == system)
        print(f"  - {system}: {count} jeux")


if __name__ == "__main__":
    main()

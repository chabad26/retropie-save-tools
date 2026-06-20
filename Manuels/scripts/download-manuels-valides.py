#!/usr/bin/env python3

from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import argparse
import csv
import re
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime

HOME = Path.home()
MANUALS_ROOT = HOME / "RetroPie" / "manuals"
GAMELISTS_ROOT = HOME / ".emulationstation" / "gamelists"


def safe_filename(name: str) -> str:
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


def download_pdf(url: str, destination: Path) -> bool:
    destination.parent.mkdir(parents=True, exist_ok=True)

    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
        },
    )

    try:
        with urlopen(request, timeout=30) as response:
            content_type = response.headers.get("Content-Type", "").lower()
            data = response.read()

    except (HTTPError, URLError, TimeoutError) as error:
        print(f"❌ Téléchargement impossible : {url}")
        print(f"   {error}")
        return False

    if not data.startswith(b"%PDF"):
        print(f"⚠️ Pas un PDF valide : {url}")
        print(f"   Content-Type : {content_type}")
        return False

    destination.write_bytes(data)
    print(f"✅ PDF téléchargé : {destination}")
    return True


def update_gamelist(system: str, mappings: dict[str, Path]) -> None:
    gamelist = GAMELISTS_ROOT / system / "gamelist.xml"

    if not gamelist.is_file():
        print(f"⚠️ Gamelist introuvable : {gamelist}")
        return

    backup = gamelist.with_name(
        f"gamelist.xml.bak-manuals-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    )

    shutil.copy2(gamelist, backup)

    tree = ET.parse(gamelist)
    root = tree.getroot()

    updated = 0

    for game in root.findall("game"):
        name_node = game.find("name")

        if name_node is None or not name_node.text:
            continue

        original_name = name_node.text.strip()

        if original_name not in mappings:
            continue

        manual_path = mappings[original_name]

        manual_node = game.find("manual")

        if manual_node is None:
            manual_node = ET.SubElement(game, "manual")

        manual_node.text = str(manual_path)
        updated += 1

    try:
        ET.indent(tree, space="  ")
    except AttributeError:
        pass

    temporary = gamelist.with_name("gamelist.xml.tmp")
    tree.write(temporary, encoding="utf-8", xml_declaration=True)

    ET.parse(temporary)
    temporary.replace(gamelist)

    print(f"✅ Gamelist mise à jour : {gamelist}")
    print(f"   Entrées <manual> : {updated}")
    print(f"   Backup : {backup}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_file", help="CSV avec colonne manual_url")
    args = parser.parse_args()

    csv_path = Path(args.csv_file).expanduser()

    if not csv_path.is_file():
        raise SystemExit(f"CSV introuvable : {csv_path}")

    with csv_path.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))

    mappings_by_system = {}

    for row in rows:
        system = row.get("system", "").strip()
        original_name = row.get("original_name", "").strip()
        search_name = row.get("search_name", "").strip()
        url = row.get("manual_url", "").strip()

        if not system or not original_name or not search_name or not url:
            continue

        if not url.lower().startswith(("http://", "https://")):
            print(f"⚠️ URL ignorée : {url}")
            continue

        filename = safe_filename(search_name) + ".pdf"
        destination = MANUALS_ROOT / system / filename

        if destination.exists() and destination.stat().st_size > 0:
            print(f"OK déjà présent : {destination}")
            success = True
        else:
            success = download_pdf(url, destination)

        if success:
            mappings_by_system.setdefault(system, {})[original_name] = destination

    for system, mappings in mappings_by_system.items():
        update_gamelist(system, mappings)

    print()
    print("🎮 Terminé.")


if __name__ == "__main__":
    main()

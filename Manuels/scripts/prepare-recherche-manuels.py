python3 <<'PY'
from pathlib import Path
import csv
import re

HOME = Path.home()

INPUT_CSV = HOME / "liste-jeux-pour-manuels.csv"
OUTPUT_CSV = HOME / "liste-jeux-pour-manuels-clean.csv"

def clean_game_name(name: str) -> str:
    original = name.strip()

    name = original

    # Tags entre crochets : [!], [f1], [b], etc.
    name = re.sub(r"\[[^\]]*\]", "", name)

    # Parenthèses purement numériques : (61959)
    name = re.sub(r"\(\d+\)", "", name)

    # Tags techniques / régions / versions
    name = re.sub(
        r"\((USA|Europe|E|J|U|F|G|I|S|M\d+|V[\d.]+|Rev\s*\d+|Beta|Proto|Demo|Sample|Alt|Hack|Translation|Unl)[^)]*\)",
        "",
        name,
        flags=re.IGNORECASE,
    )

    # Si une parenthèse contient seulement des tags collés, on enlève aussi
    name = re.sub(r"\((E|U|J|USA|Europe|M\d+|V[\d.]+)\)", "", name, flags=re.IGNORECASE)

    name = name.replace(" : ", " ")
    name = name.replace(":", " ")
    name = name.replace(" - ", " ")
    name = name.replace("_", " ")

    name = re.sub(r"\s+", " ", name)
    name = name.strip()

    return name if name else original

def build_query(system: str, clean_name: str) -> str:
    system_keywords = {
        "coleco": "colecovision",
        "dreamcast": "sega dreamcast",
        "gamegear": "sega game gear",
        "gb": "game boy",
        "gba": "game boy advance",
        "gbc": "game boy color",
        "gc": "gamecube",
        "mastersystem": "sega master system",
        "megadrive": "sega genesis mega drive",
        "n64": "nintendo 64",
        "neogeo": "neo geo",
        "nes": "nintendo entertainment system",
        "ps2": "playstation 2",
        "ps3": "playstation 3",
        "psx": "playstation",
        "saturn": "sega saturn",
        "sega32x": "sega 32x",
        "segacd": "sega cd",
        "snes": "super nintendo",
        "switch": "nintendo switch",
        "vectrex": "vectrex",
        "virtualboy": "virtual boy",
        "wii": "nintendo wii",
        "xbox": "xbox",
        "xbox360": "xbox 360",
    }

    platform = system_keywords.get(system, system)
    return f"{clean_name} {platform} manual pdf"

with INPUT_CSV.open("r", encoding="utf-8", newline="") as file:
    reader = csv.DictReader(file)
    rows = list(reader)

output_rows = []

for row in rows:
    system = row["system"]
    original_name = row["name"]
    clean_name = clean_game_name(original_name)

    row["search_name"] = clean_name
    row["search_query"] = build_query(system, clean_name)

    output_rows.append(row)

with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=list(output_rows[0].keys()))
    writer.writeheader()
    writer.writerows(output_rows)

print(f"✅ CSV nettoyé : {OUTPUT_CSV}")
print(f"Jeux traités : {len(output_rows)}")
PY

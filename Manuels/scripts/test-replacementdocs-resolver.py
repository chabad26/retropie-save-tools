#!/usr/bin/env python3

from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import argparse
import re

BASE = "https://files.replacementdocs.com"

SYSTEM_MAP = {
    "nes": ["NES"],
    "snes": ["SNES", "Super_Nintendo"],
    "megadrive": ["Mega_Drive", "Genesis"],
    "genesis": ["Genesis", "Mega_Drive"],
    "mastersystem": ["Master_System", "Sega_Master_System"],
    "saturn": ["Saturn", "Sega_Saturn"],
    "dreamcast": ["Dreamcast", "Sega_Dreamcast"],
    "n64": ["Nintendo_64", "N64"],
    "gb": ["Game_Boy"],
    "gbc": ["Game_Boy_Color"],
    "gba": ["Game_Boy_Advance"],
    "gc": ["GameCube", "Game_Cube"],
    "psx": ["PlayStation", "PlayStation_1", "PSX"],
    "ps2": ["PlayStation_2", "PS2"],
    "xbox": ["Xbox"],
    "xbox360": ["Xbox_360", "Xbox360"],
}


LANG_VARIANTS = [
    "French_Manual",
    "Manual",
    "UK_Manual",
    "US_Manual",
    "JP_Manual",
    "Japanese_Manual",
    "English_Manual",
]


def clean_name(name: str) -> str:
    name = re.sub(r"\([^)]*\)", " ", name)
    name = re.sub(r"\[[^\]]*\]", " ", name)
    name = name.replace("&", "and")
    name = re.sub(r"[^A-Za-z0-9]+", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_")


def candidates(game: str, system: str):
    game_slug = clean_name(game)
    platforms = SYSTEM_MAP.get(system.lower(), [clean_name(system)])

    for platform in platforms:
        for lang in LANG_VARIANTS:
            filename = f"{game_slug}_-_{lang}_-_{platform}.pdf"
            yield f"{BASE}/{quote(filename)}", filename


def is_pdf_url(url: str) -> bool:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"}, method="HEAD")

    try:
        with urlopen(req, timeout=15) as response:
            content_type = response.headers.get("Content-Type", "").lower()
            size = response.headers.get("Content-Length", "?")
            return "pdf" in content_type or url.lower().endswith(".pdf")
    except HTTPError as error:
        return False
    except (URLError, TimeoutError):
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("system")
    parser.add_argument("game")
    args = parser.parse_args()

    print(f"🎮 Jeu : {args.game}")
    print(f"🕹️ Système : {args.system}")
    print()

    for url, filename in candidates(args.game, args.system):
        print("Test:", filename)
        if is_pdf_url(url):
            print("✅ TROUVÉ")
            print(url)
            return

    print("❌ Aucun PDF trouvé")


if __name__ == "__main__":
    main()

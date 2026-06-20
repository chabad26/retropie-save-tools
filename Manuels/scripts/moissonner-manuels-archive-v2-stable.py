#!/usr/bin/env python3

from pathlib import Path
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from datetime import datetime
import argparse
import csv
import json
import re
import shutil
import time
import xml.etree.ElementTree as ET


HOME = Path.home()

INPUT_CSV = HOME / "liste-jeux-pour-manuels-clean.csv"
MANUALS_ROOT = HOME / "RetroPie" / "manuals"
GAMELISTS_ROOT = HOME / ".emulationstation" / "gamelists"
REPORT_PATH = Path("/home/retropie/Documents/save_retropie/Manuels/rapports/rapport-manuels-archive.csv")

ARCHIVE_SEARCH = "https://archive.org/advancedsearch.php"
ARCHIVE_METADATA = "https://archive.org/metadata"
ARCHIVE_DOWNLOAD = "https://archive.org/download"

USER_AGENT = "Mozilla/5.0 RetroPieManualHarvester/2.0"


PLATFORM_KEYWORDS = {
    "coleco": ["coleco", "colecovision"],
    "dreamcast": ["dreamcast"],
    "gamegear": ["game gear", "gamegear"],
    "gb": ["game boy", "gameboy"],
    "gba": ["game boy advance", "gba"],
    "gbc": ["game boy color", "gbc"],
    "gc": ["gamecube", "game cube"],
    "mastersystem": ["master system"],
    "megadrive": ["mega drive", "megadrive", "genesis"],
    "n64": ["nintendo 64", "n64"],
    "neogeo": ["neo geo", "neogeo"],
    "nes": ["nes", "nintendo entertainment system"],
    "ps2": ["playstation 2", "ps2"],
    "ps3": ["playstation 3", "ps3"],
    "psx": ["playstation", "ps1", "psx"],
    "saturn": ["saturn", "sega saturn"],
    "sega32x": ["32x", "sega 32x"],
    "segacd": ["sega cd", "mega cd"],
    "snes": ["snes", "super nintendo", "super nes"],
    "switch": ["switch", "nintendo switch"],
    "vectrex": ["vectrex"],
    "virtualboy": ["virtual boy", "virtualboy"],
    "wii": ["wii", "nintendo wii"],
    "xbox": ["xbox"],
    "xbox360": ["xbox 360", "xbox360"],
}


FR_WORDS = (
    "francais",
    "français",
    "french",
    "france",
    "fra",
    "manuel",
    "notice",
    "mode d'emploi",
    "mode emploi",
)

EN_WORDS = (
    "english",
    "eng",
    "usa",
    "manual",
    "instruction booklet",
    "instructions",
)

BAD_WORDS = (
    "strategy",
    "guide",
    "walkthrough",
    "cheat",
    "tips",
    "prima",
    "brady",
    "solution",
    "soluce",
    "magazine",
    "pdfdrive",
    "official movie magazine",
    "lost world",
    "movie",
    "poster",
    "box",
    "cover",
    "artwork",
    "soundtrack",
    "spieleberater",
    "pistas",
    "libro de pistas",
    "hint",
    "hints",
    "clue",
    "clues",
    "player's guide",
    "players guide",
    "nintendo player's guide",
    "encrypted",
    "ops",
    "operator",
    "operation",
    "arcademanual",
    "arcade manual",
    "novel",
    "roman",
    "book",
    "crichton",
)

def http_json(url: str) -> dict:
    request = Request(url, headers={"User-Agent": USER_AGENT})

    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def http_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT})

    with urlopen(request, timeout=60) as response:
        return response.read()


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


def normalize(text: str) -> str:
    text = text.lower()
    text = text.replace("’", "'")
    text = re.sub(r"[^a-z0-9àâçéèêëîïôûùüÿñæœ' ]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def important_tokens(name: str) -> list[str]:
    stop = {
        "the",
        "and",
        "of",
        "a",
        "an",
        "la",
        "le",
        "les",
        "de",
        "des",
        "du",
    }

    roman_or_number = {
        "2",
        "3",
        "4",
        "5",
        "ii",
        "iii",
        "iv",
        "v",
        "vi",
    }

    tokens = []

    for token in re.split(r"\s+", normalize(name)):
        if not token:
            continue

        if token in stop:
            continue

        if len(token) < 3 and token not in roman_or_number:
            continue

        tokens.append(token)

    return tokens

def build_queries(search_name: str, system: str) -> list[str]:
    tokens = important_tokens(search_name)
    token_query = " ".join(tokens[:5])

    queries = [
        f'title:"{search_name}" AND mediatype:texts',
        f'"{search_name}" AND mediatype:texts',
        f'({search_name}) AND (manual OR manuel OR notice) AND mediatype:texts',
    ]

    if token_query:
        queries.append(
            f'({token_query}) AND (manual OR manuel OR notice) AND mediatype:texts'
        )

        queries.append(
            f'({token_query}) AND mediatype:texts'
        )

    # Fallback très large, utile pour les collections Archive.
    queries.append(
        f'({search_name})'
    )

    return queries


def archive_search(query: str, rows: int, debug: bool = False) -> list[dict]:
    params = {
        "q": query,
        "fl[]": [
            "identifier",
            "title",
            "description",
            "language",
            "subject",
            "collection",
        ],
        "sort[]": "downloads desc",
        "rows": str(rows),
        "page": "1",
        "output": "json",
    }

    url = ARCHIVE_SEARCH + "?" + urlencode(params, doseq=True)

    if debug:
        print(f"    URL : {url}")

    try:
        data = http_json(url)
    except Exception as error:
        print(f"    ❌ Recherche impossible : {error}")
        return []

    docs = data.get("response", {}).get("docs", [])

    if debug:
        print(f"    Résultats : {len(docs)}")

    return docs


def get_metadata(identifier: str) -> dict | None:
    url = f"{ARCHIVE_METADATA}/{quote(identifier)}"

    try:
        return http_json(url)
    except Exception:
        return None


def language_points(text: str, preferred: str) -> tuple[int, str]:
    raw = text.lower()

    fr_hits = sum(1 for word in FR_WORDS if word in raw)
    en_hits = sum(1 for word in EN_WORDS if word in raw)

    if fr_hits:
        detected = "fr"
    elif en_hits:
        detected = "en"
    else:
        detected = "unknown"

    score = 0

    if detected == "fr":
        score += 120 if preferred == "fr" else 60

    if detected == "en":
        score += 70 if preferred == "fr" else 120

    score += fr_hits * 10
    score += en_hits * 6

    return score, detected


def score_candidate(
    search_name: str,
    system: str,
    item_text: str,
    filename: str,
    preferred_language: str,
) -> tuple[int, str]:
    full_text = f"{item_text} {filename}"
    full_norm = normalize(full_text)
    file_norm = normalize(filename)
    tokens = important_tokens(search_name)
    search_norm = normalize(search_name)

    if "jurassic park" in search_norm:
        jurassic_bad = {
            "lost world",
            "movie",
            "magazine",
            "comic",
            "comics",
            "return to",
            "crichton",
            "pdfdrive",
        }

        for bad in jurassic_bad:
            if bad in full_norm and bad not in search_norm:
                return -999, "jurassic_false_positive"

    matched_in_file = sum(
        1 for token in tokens
        if token in file_norm
    )

    if tokens and matched_in_file == 0:
        return -999, "rejected"

    if len(tokens) >= 2 and matched_in_file < 2:
        return -999, "rejected"

    hard_reject_words = {
        "pdfdrive",
        "official movie magazine",
        "lost world",
        "movie",
        "encrypted",
        "arcademanual",
        "arcade",
        "ops",
        "operator",
        "operation",
        "crichton",
        "novel",
        "roman",
        "book",
        "comic",
        "comics",
        "return to",
        "issue",
        "spieleberater",
        "pistas",
        "libro",
        "guide",
        "player's guide",
        "players guide",
    }

    for word in hard_reject_words:
        if word in full_norm:
            return -999, "hard_reject"

    file_words = set(file_norm.split())
    search_words = set(search_norm.split())

    simple_sequel_markers = {
        "2", "3", "4", "5",
        "ii", "iii", "iv", "v",
    }

    for marker in simple_sequel_markers:
        if marker in file_words and marker not in search_words:
            return -999, "wrong_sequel"

    phrase_sequel_markers = {
        "part 2",
        "part ii",
        "chaos continues",
    }

    for marker in phrase_sequel_markers:
        if marker in file_norm and marker not in search_norm:
            return -999, "wrong_sequel"

    score = 0

    for token in tokens:
        if token in full_norm:
            score += 12

        if token in file_norm:
            score += 25

    if search_norm in full_norm:
        score += 80

    if search_norm in file_norm:
        score += 120

    platform_hit = False

    for platform_word in PLATFORM_KEYWORDS.get(system, [system]):
        if normalize(platform_word) in full_norm:
            score += 25
            platform_hit = True

    manual_hit = (
        "manual" in full_norm
        or "manuel" in full_norm
        or "notice" in full_norm
        or "instruction" in full_norm
        or "instrucciones" in full_norm
    )

    if "manual" in full_norm:
        score += 40

    if "manuel" in full_norm or "notice" in full_norm:
        score += 60

    if "instruction" in full_norm or "instrucciones" in full_norm:
        score += 25

    if not manual_hit and not platform_hit and search_norm not in file_norm:
        return -999, "weak_context"

    lang_score, detected_language = language_points(
        full_text,
        preferred_language,
    )

    score += lang_score

    for bad in BAD_WORDS:
        if bad in full_norm:
            score -= 120

    if filename.lower().endswith("_text.pdf"):
        score -= 20

    return score, detected_language


def find_best_pdf(
    search_name: str,
    system: str,
    preferred_language: str,
    rows: int,
    debug: bool,
) -> dict | None:
    seen_identifiers = set()
    docs = []

    for query in build_queries(search_name, system):
        if debug:
            print(f"  Requête : {query}")

        found = archive_search(query, rows, debug=debug)

        for doc in found:
            identifier = doc.get("identifier", "")

            if identifier and identifier not in seen_identifiers:
                seen_identifiers.add(identifier)
                docs.append(doc)

        if len(docs) >= rows:
            break

        time.sleep(0.3)

    candidates = []

    for doc in docs:
        identifier = doc.get("identifier", "")

        if not identifier:
            continue

        metadata = get_metadata(identifier)

        if not metadata:
            continue

        meta = metadata.get("metadata", {})
        files = metadata.get("files", [])

        item_text = " ".join(
            str(value)
            for value in (
                identifier,
                doc.get("title", ""),
                doc.get("description", ""),
                doc.get("language", ""),
                doc.get("subject", ""),
                meta.get("title", ""),
                meta.get("description", ""),
                meta.get("language", ""),
                meta.get("subject", ""),
                meta.get("collection", ""),
            )
        )

        for file_info in files:
            filename = file_info.get("name", "")

            if not filename.lower().endswith(".pdf"):
                continue

            score, detected_language = score_candidate(
                search_name,
                system,
                item_text,
                filename,
                preferred_language,
            )

            download_url = (
                f"{ARCHIVE_DOWNLOAD}/"
                f"{quote(identifier)}/"
                f"{quote(filename)}"
            )

            candidates.append({
                "score": score,
                "identifier": identifier,
                "archive_title": doc.get("title", ""),
                "filename": filename,
                "url": download_url,
                "language": detected_language,
            })

        time.sleep(0.2)

    if not candidates:
        return None

    candidates.sort(key=lambda item: item["score"], reverse=True)
    best = candidates[0]

    if debug:
        print("  Top candidats :")
        for candidate in candidates[:5]:
            print(
                f"    {candidate['score']:4} | "
                f"{candidate['language']:7} | "
                f"{candidate['identifier']} | "
                f"{candidate['filename']}"
            )

    if best["score"] < 70:
        return None

    return best


def download_pdf(url: str, destination: Path) -> bool:
    try:
        data = http_bytes(url)
    except (HTTPError, URLError, TimeoutError) as error:
        print(f"  ❌ Téléchargement impossible : {error}")
        return False

    if not data.startswith(b"%PDF"):
        print("  ⚠️ Fichier non PDF ignoré")
        return False

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    return True


def update_gamelist(system: str, mappings: dict[str, Path]) -> None:
    if not mappings:
        return

    gamelist = GAMELISTS_ROOT / system / "gamelist.xml"

    if not gamelist.is_file():
        print(f"⚠️ Gamelist absente : {gamelist}")
        return

    backup = gamelist.with_name(
        f"gamelist.xml.bak-archive-manuals-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
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

        manual_node = game.find("manual")

        if manual_node is None:
            manual_node = ET.SubElement(game, "manual")

        manual_node.text = str(mappings[original_name])
        updated += 1

    try:
        ET.indent(tree, space="  ")
    except AttributeError:
        pass

    tmp = gamelist.with_name("gamelist.xml.tmp")
    tree.write(tmp, encoding="utf-8", xml_declaration=True)
    ET.parse(tmp)
    tmp.replace(gamelist)

    print(f"✅ Gamelist mise à jour : {gamelist}")
    print(f"   Entrées <manual> : {updated}")
    print(f"   Backup : {backup}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("system")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--language", choices=["fr", "en"], default="fr")
    parser.add_argument("--rows", type=int, default=20)
    parser.add_argument("--sleep", type=float, default=0.8)
    parser.add_argument("--debug", action="store_true")

    args = parser.parse_args()

    with INPUT_CSV.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        rows = [row for row in reader if row["system"] == args.system]

    if args.limit:
        rows = rows[:args.limit]

    report_rows = []
    mappings = {}

    print(f"🎮 Système : {args.system}")
    print(f"🎯 Jeux : {len(rows)}")
    print(f"📥 Download : {'oui' if args.download else 'dry-run'}")
    print()

    for index, row in enumerate(rows, start=1):
        original_name = row["name"]
        search_name = row["search_name"]
        destination = (
            MANUALS_ROOT
            / args.system
            / (safe_filename(search_name) + ".pdf")
        )

        print(f"[{index}/{len(rows)}] {original_name}")
        print(f"  Nom propre : {search_name}")

        if destination.exists() and destination.stat().st_size > 0:
            print(f"  OK déjà présent : {destination}")
            mappings[original_name] = destination

            report_rows.append({
                "system": args.system,
                "original_name": original_name,
                "search_name": search_name,
                "status": "already_exists",
                "language": "",
                "score": "",
                "identifier": "",
                "archive_title": "",
                "filename": "",
                "url": "",
                "destination": str(destination),
            })

            continue

        best = find_best_pdf(
            search_name,
            args.system,
            args.language,
            args.rows,
            args.debug,
        )

        if best is None and args.language == "fr":
            best = find_best_pdf(
                search_name,
                args.system,
                "en",
                args.rows,
                args.debug,
            )

        if best is None:
            print("  ❌ Rien trouvé")
            status = "not_found"
            report = {
                "system": args.system,
                "original_name": original_name,
                "search_name": search_name,
                "status": status,
                "language": "",
                "score": "",
                "identifier": "",
                "archive_title": "",
                "filename": "",
                "url": "",
                "destination": str(destination),
            }
            report_rows.append(report)
            time.sleep(args.sleep)
            continue

        print(f"  ✅ Candidat : {best['filename']}")
        print(f"  Langue : {best['language']}")
        print(f"  Score : {best['score']}")
        print(f"  URL : {best['url']}")

        status = "found"

        if args.download:
            if download_pdf(best["url"], destination):
                print(f"  📄 Téléchargé : {destination}")
                mappings[original_name] = destination
                status = "downloaded"
            else:
                status = "download_failed"

        report_rows.append({
            "system": args.system,
            "original_name": original_name,
            "search_name": search_name,
            "status": status,
            "language": best["language"],
            "score": best["score"],
            "identifier": best["identifier"],
            "archive_title": best["archive_title"],
            "filename": best["filename"],
            "url": best["url"],
            "destination": str(destination),
        })

        time.sleep(args.sleep)

    with REPORT_PATH.open("w", encoding="utf-8", newline="") as file:
        fieldnames = [
            "system",
            "original_name",
            "search_name",
            "status",
            "language",
            "score",
            "identifier",
            "archive_title",
            "filename",
            "url",
            "destination",
        ]

        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(report_rows)

    print()
    print(f"📊 Rapport : {REPORT_PATH}")

    if args.download:
        update_gamelist(args.system, mappings)

    print()
    print("🌾 Moisson terminée.")


if __name__ == "__main__":
    main()

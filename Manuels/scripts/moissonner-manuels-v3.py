#!/usr/bin/env python3

from pathlib import Path
from urllib.parse import urljoin, quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from html.parser import HTMLParser
from datetime import datetime
import argparse
import csv
import importlib.util
import re
import shutil
import time
import xml.etree.ElementTree as ET


HOME = Path.home()

INPUT_CSV = HOME /Documents/save_retropie/Manuels/ "liste-jeux-pour-manuels-clean.csv"
MANUALS_ROOT = HOME /Documents/save_retropie/Manuels/ "RetroPie" / "manuals"
GAMELISTS_ROOT = HOME /Documents/save_retropie/Manuels/ ".emulationstation" / "gamelists"
REPORT_PATH = HOME /Documents/save_retropie/Manuels/ "rapport-manuels-v3.csv"

V2_SCRIPT = HOME /Documents/save_retropie/Manuels/ "moissonner-manuels-archive-v2.py"

CACHE_DIR = HOME / ".cache" / "retropie-manuals"
ABANDONWARE_INDEX = CACHE_DIR / "abandonware-consoles-index.csv"

USER_AGENT = "Mozilla/5.0 RetroPieManualHarvester/3.0"

ABANDONWARE_BASE = "https://www.abandonware-france.org"
ABANDONWARE_START = "https://www.abandonware-france.org/ltf_manuels/lst_manuels.php?manuels=consoles"


def load_v2():
    if not V2_SCRIPT.is_file():
        raise SystemExit(f"Script V2 introuvable : {V2_SCRIPT}")

    spec = importlib.util.spec_from_file_location("archive_v2", V2_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.current_href = None
        self.current_text = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return

        attrs = dict(attrs)
        href = attrs.get("href")

        if href:
            self.current_href = href
            self.current_text = []

    def handle_data(self, data):
        if self.current_href is not None:
            self.current_text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() != "a":
            return

        if self.current_href is not None:
            self.links.append({
                "href": self.current_href,
                "text": " ".join(self.current_text).strip(),
            })

        self.current_href = None
        self.current_text = []


def http_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})

    with urlopen(request, timeout=35) as response:
        raw = response.read()

    return raw.decode("utf-8", errors="replace")


def http_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT})

    with urlopen(request, timeout=60) as response:
        return response.read()


def normalize(text: str) -> str:
    text = text.lower()
    text = text.replace("’", "'")
    text = re.sub(r"[^a-z0-9àâçéèêëîïôûùüÿñæœ' ]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def important_tokens(name: str) -> list[str]:
    stop = {
        "the", "and", "of", "a", "an",
        "la", "le", "les", "de", "des", "du",
    }

    useful_short = {
        "2", "3", "4", "5",
        "ii", "iii", "iv", "v", "vi",
    }

    tokens = []

    for token in re.split(r"\s+", normalize(name)):
        if not token:
            continue

        if token in stop:
            continue

        if len(token) < 3 and token not in useful_short:
            continue

        tokens.append(token)

    return tokens


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


def parse_links(url: str) -> list[dict]:
    html = http_text(url)
    parser = LinkParser()
    parser.feed(html)

    links = []

    for link in parser.links:
        href = urljoin(url, link["href"])
        text = link["text"]

        links.append({
            "url": href,
            "text": text,
        })

    return links


def build_abandonware_index(max_pages: int, sleep: float, force: bool = False) -> list[dict]:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if ABANDONWARE_INDEX.is_file() and not force:
        with ABANDONWARE_INDEX.open("r", encoding="utf-8", newline="") as file:
            return list(csv.DictReader(file))

    print("📚 Construction index Abandonware France...")

    queue = [ABANDONWARE_START]
    seen_pages = set()
    manual_entries = {}

    while queue and len(seen_pages) < max_pages:
        url = queue.pop(0)

        if url in seen_pages:
            continue

        seen_pages.add(url)

        try:
            links = parse_links(url)
        except Exception as error:
            print(f"  ⚠️ Page ignorée : {url}")
            print(f"     {error}")
            continue

        print(f"  Page {len(seen_pages)}/{max_pages} : {url}")

        for link in links:
            link_url = link["url"]
            link_text = link["text"]

            if "lst_manuels.php" in link_url and "manuels=consoles" in link_url:
                if link_url not in seen_pages and link_url not in queue:
                    queue.append(link_url)

            if "manuels.php?id_manuel=" in link_url:
                key = link_url.split("id_manuel=")[-1].split("&")[0]

                if key not in manual_entries:
                    manual_entries[key] = {
                        "title": link_text,
                        "detail_url": link_url,
                    }

        time.sleep(sleep)

    rows = list(manual_entries.values())

    with ABANDONWARE_INDEX.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["title", "detail_url"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Index Abandonware : {len(rows)} entrées")
    print(f"   Cache : {ABANDONWARE_INDEX}")

    return rows


def score_title(search_name: str, title: str) -> int:
    title_norm = normalize(title)
    search_norm = normalize(search_name)
    tokens = important_tokens(search_name)

    score = 0

    if search_norm == title_norm:
        score += 300

    if search_norm in title_norm:
        score += 180

    matched = 0

    for token in tokens:
        if token in title_norm:
            matched += 1
            score += 35

    if tokens and matched < max(1, min(2, len(tokens))):
        return -999

    bad_words = (
        "solution",
        "soluce",
        "guide",
        "tips",
        "astuces",
        "trucs",
        "magazine",
        "catalogue",
    )

    for word in bad_words:
        if word in title_norm:
            score -= 200

    return score


def find_abandonware(search_name: str, system: str, index_rows: list[dict]) -> dict | None:
    candidates = []

    for row in index_rows:
        title = row.get("title", "")
        detail_url = row.get("detail_url", "")

        score = score_title(search_name, title)

        if score < 80:
            continue

        candidates.append({
            "source": "abandonware",
            "title": title,
            "score": score + 120,
            "language": "fr",
            "detail_url": detail_url,
            "url": detail_url,
            "filename": title,
        })

    if not candidates:
        return None

    candidates.sort(key=lambda item: item["score"], reverse=True)
    return candidates[0]


def find_download_link_in_abandonware_detail(detail_url: str) -> str | None:
    links = parse_links(detail_url)

    preferred = []

    for link in links:
        url = link["url"]
        text = normalize(link["text"])

        haystack = normalize(url + " " + text)

        if ".pdf" in haystack:
            preferred.append(url)
            continue

        if "download" in haystack or "telecharger" in haystack or "télécharger" in haystack:
            preferred.append(url)
            continue

        if "manuel" in haystack and ("voir" in haystack or "download" in haystack):
            preferred.append(url)

    if preferred:
        return preferred[0]

    return None


def is_pdf(data: bytes) -> bool:
    return data.startswith(b"%PDF")


def download_any_pdf(candidate: dict, destination: Path, sleep: float) -> bool:
    source = candidate["source"]

    if source == "archive":
        url = candidate["url"]

        try:
            data = http_bytes(url)
        except (HTTPError, URLError, TimeoutError) as error:
            print(f"  ❌ Archive download impossible : {error}")
            return False

        if not is_pdf(data):
            print("  ⚠️ Archive : fichier non PDF")
            return False

        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        return True

    if source == "abandonware":
        detail_url = candidate["detail_url"]

        try:
            download_url = find_download_link_in_abandonware_detail(detail_url)
        except Exception as error:
            print(f"  ❌ Abandonware détail impossible : {error}")
            return False

        if not download_url:
            print("  ⚠️ Abandonware : lien PDF introuvable dans la fiche")
            return False

        time.sleep(sleep)

        try:
            data = http_bytes(download_url)
        except (HTTPError, URLError, TimeoutError) as error:
            print(f"  ❌ Abandonware download impossible : {error}")
            return False

        if not is_pdf(data):
            print("  ⚠️ Abandonware : le lien ne retourne pas un PDF direct")
            return False

        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        candidate["url"] = download_url
        return True

    return False


def update_gamelist(system: str, mappings: dict[str, Path]) -> None:
    if not mappings:
        return

    gamelist = GAMELISTS_ROOT / system / "gamelist.xml"

    if not gamelist.is_file():
        print(f"⚠️ Gamelist absente : {gamelist}")
        return

    backup = gamelist.with_name(
        f"gamelist.xml.bak-manuals-v3-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
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


def archive_candidate(v2, search_name: str, system: str, language: str, rows: int, debug: bool) -> dict | None:
    best = v2.find_best_pdf(
        search_name,
        system,
        language,
        rows,
        debug,
    )

    if best is None and language == "fr":
        best = v2.find_best_pdf(
            search_name,
            system,
            "en",
            rows,
            debug,
        )

    if best is None:
        return None

    return {
        "source": "archive",
        "title": best.get("archive_title", ""),
        "score": best.get("score", 0),
        "language": best.get("language", best.get("detected_language", "unknown")),
        "url": best.get("url", best.get("download_url", "")),
        "filename": best.get("filename", ""),
        "identifier": best.get("identifier", ""),
    }


def choose_best(candidates: list[dict]) -> dict | None:
    if not candidates:
        return None

    candidates.sort(key=lambda item: item.get("score", 0), reverse=True)
    return candidates[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("system")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--language", choices=["fr", "en"], default="fr")
    parser.add_argument("--rows", type=int, default=20)
    parser.add_argument("--sleep", type=float, default=1.0)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--refresh-abandonware", action="store_true")
    parser.add_argument("--abandonware-pages", type=int, default=12)
    parser.add_argument(
        "--sources",
        default="archive,abandonware",
        help="Sources : archive,abandonware,replacementdocs",
    )

    args = parser.parse_args()

    source_order = [
        source.strip().lower()
        for source in args.sources.split(",")
        if source.strip()
    ]

    v2 = None

    if "archive" in source_order:
        v2 = load_v2()

    abandonware_index = []

    if "abandonware" in source_order:
        abandonware_index = build_abandonware_index(
            max_pages=args.abandonware_pages,
            sleep=args.sleep,
            force=args.refresh_abandonware,
        )

    with INPUT_CSV.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        rows = [row for row in reader if row["system"] == args.system]

    if args.limit:
        rows = rows[:args.limit]

    print(f"🎮 Système : {args.system}")
    print(f"🎯 Jeux : {len(rows)}")
    print(f"🔎 Sources : {', '.join(source_order)}")
    print(f"📥 Download : {'oui' if args.download else 'dry-run'}")
    print()

    mappings = {}
    report_rows = []

    for index, row in enumerate(rows, start=1):
        original_name = row["name"]
        search_name = row["search_name"]
        destination = MANUALS_ROOT / args.system / (safe_filename(search_name) + ".pdf")

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
                "source": "",
                "language": "",
                "score": "",
                "title": "",
                "filename": "",
                "url": "",
                "destination": str(destination),
            })

            continue

        candidates = []

        for source in source_order:
            candidate = None

            if source == "archive":
                candidate = archive_candidate(
                    v2,
                    search_name,
                    args.system,
                    args.language,
                    args.rows,
                    args.debug,
                )

            elif source == "abandonware":
                candidate = find_abandonware(
                    search_name,
                    args.system,
                    abandonware_index,
                )

            elif source == "replacementdocs":
                print("  ⚠️ ReplacementDocs prévu, mais désactivé pour l'instant")
                candidate = None

            if candidate:
                print(
                    f"  Candidat {source}: "
                    f"{candidate.get('filename') or candidate.get('title')} "
                    f"({candidate.get('language')}, score {candidate.get('score')})"
                )
                candidates.append(candidate)

                # Français Abandonware fiable : on peut s'arrêter.
                if source == "abandonware" and candidate.get("language") == "fr":
                    break

            time.sleep(args.sleep)

        best = choose_best(candidates)

        if not best:
            print("  ❌ Rien trouvé")

            report_rows.append({
                "system": args.system,
                "original_name": original_name,
                "search_name": search_name,
                "status": "not_found",
                "source": "",
                "language": "",
                "score": "",
                "title": "",
                "filename": "",
                "url": "",
                "destination": str(destination),
            })

            continue

        print(f"  ✅ Choix : {best['source']} | {best.get('filename') or best.get('title')}")
        print(f"  URL : {best.get('url', '')}")

        status = "found"

        if args.download:
            if download_any_pdf(best, destination, args.sleep):
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
            "source": best.get("source", ""),
            "language": best.get("language", ""),
            "score": best.get("score", ""),
            "title": best.get("title", ""),
            "filename": best.get("filename", ""),
            "url": best.get("url", ""),
            "destination": str(destination),
        })

    with REPORT_PATH.open("w", encoding="utf-8", newline="") as file:
        fieldnames = [
            "system",
            "original_name",
            "search_name",
            "status",
            "source",
            "language",
            "score",
            "title",
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
    print("🌾 Moisson V3 terminée.")


if __name__ == "__main__":
    main()

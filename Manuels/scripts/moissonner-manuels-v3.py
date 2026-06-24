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

INPUT_CSV = HOME / "Documents/save_retropie/Manuels/rapports/liste-jeux-pour-manuels-clean.csv"
MANUALS_ROOT = HOME / "Documents/save_retropie/Manuels/pdf"
GAMELISTS_ROOT = HOME / ".emulationstation/gamelists"
REPORT_PATH = HOME / "Documents/save_retropie/Manuels/rapports/rapport-manuels-v3.csv"
VALIDATED_LINKS_CSV = HOME / "Documents/save_retropie/Manuels/rapports/liens-manuels-valides.csv"

V2_SCRIPT = HOME / "Documents/save_retropie/Manuels/scripts/moissonner-manuels-archive-v2.py"

CACHE_DIR = HOME / ".cache" / "retropie-manuals"
REPLACEMENTDOCS_INDEX = CACHE_DIR / "replacementdocs-index.csv"

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"

REPLACEMENTDOCS_BASE = "https://www.replacementdocs.com"
REPLACEMENTDOCS_DOWNLOADS = "https://www.replacementdocs.com/download.php"
NOTIPIX_BASE = "https://notipix.fr"
NOTIPIX_SEARCH_API = "https://notipix.fr/wp-json/wp/v2/search?search="

# Fallback si ReplacementDocs bloque la page principale.
# À compléter au fil des tests.
REPLACEMENTDOCS_PLATFORM_IDS = {
    "snes": "16",
    "supernintendo": "16",
}


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
    request = Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
        "Referer": REPLACEMENTDOCS_BASE + "/",
    })

    with urlopen(request, timeout=35) as response:
        raw = response.read()

    return raw.decode("utf-8", errors="replace")


def http_bytes(url: str) -> bytes:
    request = Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/pdf,application/octet-stream,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
        "Referer": REPLACEMENTDOCS_BASE + "/",
    })

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



def rd_norm(value: str) -> str:
    import re
    import unicodedata

    value = value or ""
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = value.lower()

    # retire les infos de région / disque / version
    value = re.sub(r"\([^)]*\)", " ", value)
    value = re.sub(r"\[[^\]]*\]", " ", value)

    # simplifie les séparateurs
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    value = re.sub(r"\b(the|a|an|le|la|les|de|des|du)\b", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def rd_score(search_name: str, title: str) -> int:
    wanted = rd_norm(search_name)
    got = rd_norm(title)

    if not wanted or not got:
        return 0

    if wanted == got:
        return 100

    if wanted in got or got in wanted:
        return 82

    wanted_words = set(wanted.split())
    got_words = set(got.split())

    if not wanted_words:
        return 0

    common = wanted_words & got_words
    score = int((len(common) / len(wanted_words)) * 70)

    # bonus si le début colle bien
    if got.startswith(next(iter(wanted_words), "")):
        score += 5

    return score


def replacementdocs_platform_aliases(system: str) -> list[str]:
    aliases = {
        "snes": ["super nes", "super famicom"],
        "supernintendo": ["super nes", "super famicom"],
        "nes": ["nes", "famicom"],
        "n64": ["nintendo 64"],
        "gba": ["game boy advance"],
        "gbc": ["game boy color"],
        "gb": ["game boy"],
        "gameboy": ["game boy"],
        "gameboycolor": ["game boy color"],
        "gameboyadvance": ["game boy advance"],
        "genesis": ["genesis", "mega drive"],
        "megadrive": ["genesis", "mega drive"],
        "mastersystem": ["master system"],
        "gamegear": ["game gear"],
        "dreamcast": ["dreamcast"],
        "saturn": ["saturn"],
        "psx": ["playstation"],
        "ps1": ["playstation"],
        "playstation": ["playstation"],
        "ps2": ["playstation 2"],
        "ps3": ["playstation 3"],
        "psp": ["psp"],
        "psvita": ["ps vita"],
        "gamecube": ["gamecube"],
        "gc": ["gamecube"],
        "wii": ["wii"],
        "wiiu": ["wii u"],
        "xbox": ["xbox"],
        "xbox360": ["xbox 360"],
        "3do": ["3do"],
        "atarijaguar": ["jaguar"],
        "jaguar": ["jaguar"],
        "lynx": ["lynx"],
        "colecovision": ["colecovision"],
        "intellivision": ["intellivision"],
        "tg16": ["turbografx", "pc engine"],
        "pcengine": ["turbografx", "pc engine"],
    }
    key = (system or "").lower().replace("-", "").replace("_", "")
    return aliases.get(key, [key])


def replacementdocs_platform_id(system: str) -> str | None:
    import re
    from html import unescape

    key = (system or "").lower().replace("-", "").replace("_", "")

    if key in REPLACEMENTDOCS_PLATFORM_IDS:
        return REPLACEMENTDOCS_PLATFORM_IDS[key]

    try:
        html = http_text(REPLACEMENTDOCS_DOWNLOADS)
    except Exception as error:
        print(f"  ⚠️ ReplacementDocs : index principal inaccessible ({error})")
        return None

    wanted_aliases = replacementdocs_platform_aliases(system)

    # Exemple de lien : download.php?list.16=
    links = re.findall(
        r'<a\s+[^>]*href=["\']([^"\']*download\.php\?list\.(\d+)=[^"\']*)["\'][^>]*>(.*?)</a>',
        html,
        flags=re.I | re.S,
    )

    for href, platform_id, label_html in links:
        label = re.sub(r"<.*?>", " ", label_html)
        label = unescape(label)
        label_norm = rd_norm(label)

        for alias in wanted_aliases:
            alias_norm = rd_norm(alias)
            if alias_norm and alias_norm in label_norm:
                return platform_id

    return None


def build_replacementdocs_index(system: str, max_pages: int, sleep: float, force: bool = False, platform_override: str | None = None) -> list[dict]:
    import csv
    import re
    import time
    from html import unescape
    from urllib.parse import urljoin

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    cache_file = CACHE_DIR / f"replacementdocs-{system}.csv"

    if cache_file.is_file() and not force:
        with cache_file.open("r", encoding="utf-8", newline="") as file:
            return list(csv.DictReader(file))

    platform_id = platform_override or replacementdocs_platform_id(system)

    if not platform_id:
        print(f"  ⚠️ ReplacementDocs : plateforme introuvable pour {system}")
        return []

    print(f"📚 Construction index ReplacementDocs pour {system} / list.{platform_id}...")

    start_url = f"{REPLACEMENTDOCS_BASE}/download.php?list.{platform_id}="
    queue = [start_url]
    seen_pages = set()
    rows = []

    while queue and len(seen_pages) < max_pages:
        url = queue.pop(0)

        if url in seen_pages:
            continue

        seen_pages.add(url)

        try:
            html = http_text(url)
        except Exception as error:
            print(f"  ⚠️ ReplacementDocs page impossible : {error}")
            continue

        for match in re.finditer(
            r'<a\s+[^>]*href=["\']([^"\']*download\.php\?view\.(\d+)=[^"\']*)["\'][^>]*>(.*?)</a>',
            html,
            flags=re.I | re.S,
        ):
            href = match.group(1)
            doc_id = match.group(2)
            title_html = match.group(3)

            title = re.sub(r"<.*?>", " ", title_html)
            title = unescape(title)
            title = re.sub(r"\s+", " ", title).strip()

            if not title:
                continue

            detail_url = urljoin(REPLACEMENTDOCS_BASE + "/", href)

            # Fenêtre de texte autour du lien pour récupérer "Manual", "JP Manual", etc.
            start = max(0, match.start() - 120)
            end = min(len(html), match.end() + 220)
            context = re.sub(r"<.*?>", " ", html[start:end])
            context = unescape(context)
            context = re.sub(r"\s+", " ", context).strip()

            language = "en"
            lowered = context.lower()

            if " jp manual" in lowered or "japanese" in lowered:
                language = "jp"
            elif " fr manual" in lowered or "french" in lowered:
                language = "fr"

            # On garde surtout les manuals, pas les maps si possible.
            doc_type = "manual"
            if " map " in f" {lowered} ":
                doc_type = "map"

            rows.append({
                "source": "replacementdocs",
                "system": system,
                "id": doc_id,
                "title": title,
                "detail_url": detail_url,
                "url": detail_url,
                "language": language,
                "doc_type": doc_type,
                "filename": f"{title}.pdf",
            })

        # Pagination ReplacementDocs : on récupère les autres liens list.<id>...
        for href in re.findall(
            rf'href=["\']([^"\']*download\.php\?list\.{platform_id}[^"\']*)["\']',
            html,
            flags=re.I,
        ):
            next_url = urljoin(REPLACEMENTDOCS_BASE + "/", href)
            if next_url not in seen_pages and next_url not in queue:
                queue.append(next_url)

        time.sleep(sleep)

    # Déduplication par id
    unique = {}
    for row in rows:
        unique[row["id"]] = row

    rows = list(unique.values())

    with cache_file.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["source", "system", "id", "title", "detail_url", "url", "language", "doc_type", "filename"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Index ReplacementDocs : {len(rows)} entrées")
    print(f"   Cache : {cache_file}")

    return rows


def find_replacementdocs(search_name: str, system: str, max_pages: int, sleep: float, force: bool = False, platform_id: str | None = None) -> dict | None:
    rows = build_replacementdocs_index(
        system,
        max_pages=max_pages,
        sleep=sleep,
        force=force,
        platform_override=platform_id,
    )

    best = None
    best_score = 0

    for row in rows:
        if row.get("doc_type") and row["doc_type"] != "manual":
            continue

        score = rd_score(search_name, row.get("title", ""))

        # on évite les manuels JP si on cherche autre chose
        if row.get("language") == "jp":
            score -= 25

        if score > best_score:
            best = dict(row)
            best_score = score

    if not best or best_score < 45:
        return None

    best["score"] = best_score
    best["source"] = "replacementdocs"
    return best


def find_download_link_in_replacementdocs_detail(detail_url: str, doc_id: str | None = None) -> str | None:
    import re
    from urllib.parse import urljoin

    html = http_text(detail_url)

    # Liens explicites possibles dans la fiche.
    candidates = []

    for href in re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.I):
        low = href.lower()

        if ".pdf" in low:
            candidates.append(urljoin(REPLACEMENTDOCS_BASE + "/", href))

        if "download.php?" in low and (
            "download." in low or
            "get." in low or
            "file." in low
        ):
            candidates.append(urljoin(REPLACEMENTDOCS_BASE + "/", href))

    # Fallbacks e107 / ReplacementDocs probables.
    if doc_id:
        candidates.extend([
            f"{REPLACEMENTDOCS_BASE}/download.php?download.{doc_id}=",
            f"{REPLACEMENTDOCS_BASE}/download.php?download.{doc_id}",
            f"{REPLACEMENTDOCS_BASE}/download.php?get.{doc_id}=",
            f"{REPLACEMENTDOCS_BASE}/download.php?get.{doc_id}",
        ])

    seen = set()
    for url in candidates:
        if url in seen:
            continue
        seen.add(url)

        try:
            data = http_bytes(url)
        except Exception:
            continue

        if data[:4] == b"%PDF" or b"%PDF" in data[:2048]:
            return url

    return None



def download_any_pdf(candidate: dict, destination: Path, sleep: float) -> bool:
    source = candidate["source"]

    if source == "notipix":
        url = candidate["url"]

        try:
            data = google_drive_download_bytes(url)
        except Exception as error:
            print(f"  ❌ Notipix / Google Drive download impossible : {error}")
            return False

        if data[:4] != b"%PDF" and b"%PDF" not in data[:2048]:
            print("  ⚠️ Notipix : le lien Google Drive ne retourne pas un PDF direct")
            return False

        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        return True

    if source == "localcsv":
        url = candidate["url"]

        try:
            data = http_bytes(url)
        except (HTTPError, URLError, TimeoutError) as error:
            print(f"  ❌ CSV local download impossible : {error}")
            return False

        if data[:4] != b"%PDF" and b"%PDF" not in data[:2048]:
            print("  ⚠️ CSV local : fichier non PDF")
            return False

        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        return True

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

    if source == "replacementdocs":
        detail_url = candidate.get("detail_url") or candidate.get("url")
        doc_id = candidate.get("id")

        try:
            download_url = find_download_link_in_replacementdocs_detail(detail_url, doc_id)
        except (HTTPError, URLError, TimeoutError) as error:
            print(f"  ❌ ReplacementDocs détail impossible : {error}")
            return False

        if not download_url:
            print("  ⚠️ ReplacementDocs : lien PDF introuvable dans la fiche")
            return False

        time.sleep(sleep)

        try:
            data = http_bytes(download_url)
        except (HTTPError, URLError, TimeoutError) as error:
            print(f"  ❌ ReplacementDocs download impossible : {error}")
            return False

        if data[:4] != b"%PDF" and b"%PDF" not in data[:2048]:
            print("  ⚠️ ReplacementDocs : le lien ne retourne pas un PDF direct")
            return False

        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        candidate["url"] = download_url
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






def notipix_platform_slugs(system: str) -> list[str]:
    aliases = {
        "nes": ["/nintendo/nes/"],
        "famicom": ["/nintendo/famicom/"],
        "snes": ["/nintendo/super-nintendo/"],
        "supernintendo": ["/nintendo/super-nintendo/"],
        "gb": ["/nintendo/game-boy/"],
        "gameboy": ["/nintendo/game-boy/"],
        "gbc": ["/nintendo/game-boy-color/"],
        "gameboycolor": ["/nintendo/game-boy-color/"],
        "gba": ["/nintendo/game-boy-advance/"],
        "gameboyadvance": ["/nintendo/game-boy-advance/"],
        "mastersystem": ["/sega/master-system/"],
        "megadrive": ["/sega/mega-drive/"],
        "genesis": ["/sega/mega-drive/"],
        "gamegear": ["/sega/game-gear/"],
        "neogeo": ["/autres/neogeo-aes/"],
        "neogeoaes": ["/autres/neogeo-aes/"],
        "pcengine": ["/autres/pc-engine/"],
        "tg16": ["/autres/pc-engine/"],
        "virtualboy": ["/nintendo/virtual-boy/"],
    }

    key = (system or "").lower().replace("-", "").replace("_", "")
    return aliases.get(key, [])


def extract_google_drive_file_id(url: str) -> str | None:
    patterns = [
        r"drive\.google\.com/file/d/([^/]+)/",
        r"drive\.google\.com/open\?id=([^&]+)",
        r"drive\.google\.com/uc\?id=([^&]+)",
        r"id=([^&]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def google_drive_download_bytes(view_url: str) -> bytes:
    from urllib.parse import urlencode
    from urllib.request import build_opener, HTTPCookieProcessor, Request
    from http.cookiejar import CookieJar

    file_id = extract_google_drive_file_id(view_url)

    if not file_id:
        raise ValueError(f"ID Google Drive introuvable : {view_url}")

    cj = CookieJar()
    opener = build_opener(HTTPCookieProcessor(cj))

    base = "https://drive.google.com/uc?" + urlencode({
        "export": "download",
        "id": file_id,
    })

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/pdf,application/octet-stream,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    }

    response = opener.open(Request(base, headers=headers), timeout=60)
    data = response.read()

    if data[:4] == b"%PDF" or b"%PDF" in data[:2048]:
        return data

    # Google Drive peut parfois demander une confirmation.
    text = data.decode("utf-8", errors="replace")

    confirm = None

    for pattern in [
        r"confirm=([0-9A-Za-z_]+)",
        r'name="confirm"\s+value="([^"]+)"',
    ]:
        match = re.search(pattern, text)
        if match:
            confirm = match.group(1)
            break

    if confirm:
        url = "https://drive.google.com/uc?" + urlencode({
            "export": "download",
            "id": file_id,
            "confirm": confirm,
        })

        response = opener.open(Request(url, headers=headers), timeout=60)
        data = response.read()

        if data[:4] == b"%PDF" or b"%PDF" in data[:2048]:
            return data

    return data


def notipix_candidate(search_name: str, original_name: str, system: str, debug: bool = False) -> dict | None:
    import json
    from urllib.parse import quote
    from html import unescape

    slugs = notipix_platform_slugs(system)

    if not slugs:
        if debug:
            print(f"  ⚠️ Notipix : système non mappé pour {system}")
        return None

    url = NOTIPIX_SEARCH_API + quote(search_name)

    try:
        request = Request(url, headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        })
        data = json.loads(urlopen(request, timeout=30).read().decode("utf-8", errors="replace"))
    except Exception as error:
        print(f"  ⚠️ Notipix recherche impossible : {error}")
        return None

    candidates = []

    for item in data:
        title = unescape(item.get("title", "") or "")
        page_url = item.get("url", "") or ""

        if not page_url:
            continue

        # Filtre console : évite Famicom quand on demande NES, GB Color quand on demande NES, etc.
        if not any(slug in page_url for slug in slugs):
            continue

        score = rd_score(search_name, title)

        # Bonus si le titre WP colle bien au nom exact.
        if normalize(title) == normalize(search_name):
            score += 40

        if score < 45:
            continue

        candidates.append({
            "title": title,
            "page_url": page_url,
            "score": score,
        })

    if not candidates:
        return None

    candidates.sort(key=lambda item: item["score"], reverse=True)
    best = candidates[0]

    try:
        request = Request(best["page_url"], headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        })
        html = urlopen(request, timeout=30).read().decode("utf-8", errors="replace")
        html = unescape(html)
    except Exception as error:
        print(f"  ⚠️ Notipix fiche impossible : {error}")
        return None

    drive_urls = []

    for match in re.finditer(r'https?://(?:drive|docs)\.google\.com/[^"\'>\s]+', html, flags=re.I):
        drive_urls.append(match.group(0))

    # Déduplication
    seen = set()
    drive_urls = [u for u in drive_urls if not (u in seen or seen.add(u))]

    if not drive_urls:
        if debug:
            print(f"  ⚠️ Notipix : aucun lien Drive dans {best['page_url']}")
        return None

    drive_url = drive_urls[0]

    return {
        "source": "notipix",
        "title": best["title"],
        "score": best["score"] + 450,
        "language": "fr",
        "url": drive_url,
        "page_url": best["page_url"],
        "filename": f"{safe_filename(search_name)}.pdf",
    }



def local_csv_candidate(search_name: str, original_name: str, system: str) -> dict | None:
    if not VALIDATED_LINKS_CSV.is_file():
        return None

    search_norm = normalize(search_name)
    original_norm = normalize(original_name)

    try:
        with VALIDATED_LINKS_CSV.open("r", encoding="utf-8", newline="") as file:
            rows = list(csv.DictReader(file))
    except Exception as error:
        print(f"  ⚠️ CSV validé illisible : {error}")
        return None

    best = None
    best_score = -999

    for row in rows:
        if row.get("system", "").strip() != system:
            continue

        row_search = row.get("search_name", "").strip()
        row_name = row.get("name", "").strip()
        url = row.get("url", "").strip()

        if not url:
            continue

        score = 0

        if row_search and normalize(row_search) == search_norm:
            score += 300

        if row_name and normalize(row_name) == original_norm:
            score += 250

        if row_search and normalize(row_search) in search_norm:
            score += 120

        if row_search and search_norm in normalize(row_search):
            score += 120

        if score > best_score:
            best_score = score
            best = row

    if not best or best_score < 120:
        return None

    filename = best.get("filename", "").strip() or f"{safe_filename(search_name)}.pdf"

    return {
        "source": "localcsv",
        "title": best.get("search_name") or best.get("name") or search_name,
        "score": best_score + 500,
        "language": best.get("language", "unknown"),
        "url": best.get("url", ""),
        "filename": filename,
    }



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
    parser.add_argument("--language", choices=["fr", "en"], default="localcsv,notipix,archive")
    parser.add_argument("--rows", type=int, default=20)
    parser.add_argument("--sleep", type=float, default=1.0)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--refresh-replacementdocs", action="store_true")
    parser.add_argument("--replacementdocs-pages", type=int, default=12)
    parser.add_argument("--replacementdocs-platform-id", default="", help="Force un ID ReplacementDocs, ex: 16 pour SNES")
    parser.add_argument(
        "--sources",
        default="archive,replacementdocs",
        help="Sources : localcsv,notipix,archive,replacementdocs. ReplacementDocs est expérimental et peut être indisponible.",
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

    if "replacementdocs" in source_order:
        print("⚠️ ReplacementDocs est connu comme instable / potentiellement cassé. Source gardée en expérimental.")
    replacementdocs_index = []
    if not INPUT_CSV.is_file():
        raise SystemExit(
            f"❌ CSV introuvable : {INPUT_CSV}\n"
            "Lance d'abord :\n"
            "  scripts/scan-gamelists-manuels.py\n"
            "  scripts/prepare-recherche-manuels.py"
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

            if source == "localcsv":
                candidate = local_csv_candidate(
                    search_name,
                    original_name,
                    args.system,
                )

            elif source == "notipix":
                candidate = notipix_candidate(
                    search_name,
                    original_name,
                    args.system,
                    args.debug,
                )

            elif source == "archive":
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
                candidate = find_replacementdocs(
                    search_name,
                    args.system,
                    max_pages=args.replacementdocs_pages,
                    sleep=args.sleep,
                    force=args.refresh_replacementdocs,
                    platform_id=args.replacementdocs_platform_id or None,
                )

            if candidate:
                print(
                    f"  Candidat {source}: "
                    f"{candidate.get('filename') or candidate.get('title')} "
                    f"({candidate.get('language')}, score {candidate.get('score')})"
                )
                candidates.append(candidate)

                # CSV validé local : source fiable, on s'arrête.
                if source == "localcsv":
                    break

                # Notipix : source française fiable si lien trouvé.
                if source == "notipix":
                    break

                # ReplacementDocs expérimental.
                if source == "replacementdocs" and candidate.get("language") in ("fr", "en"):
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

#!/usr/bin/env python3

from pathlib import Path
import argparse
import csv
import subprocess
import sys
import xml.etree.ElementTree as ET

HOME = Path.home()

MANUALS_ROOT = HOME / "Documents/save_retropie/Manuels/pdf"
REPORT_DIR = HOME / "Documents/save_retropie/Manuels/rapports"
REPORT_CSV = REPORT_DIR / "rapport-qualite-manuels.csv"

GAMELISTS_ROOT = HOME / ".emulationstation/gamelists"

MIN_BYTES_HARD = 30 * 1024
MIN_BYTES_WARN = 100 * 1024

BIG_BYTES_WARN = 50 * 1024 * 1024
BIG_BYTES_HARD = 100 * 1024 * 1024

MAX_BYTES_PER_PAGE_WARN = 5 * 1024 * 1024
MAX_BYTES_PER_PAGE_HARD = 10 * 1024 * 1024


def human_size(size: int) -> str:
    units = ["o", "Ko", "Mo", "Go"]

    value = float(size)

    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "o":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024

    return f"{size} o"


def run_pdfinfo(path: Path) -> dict:
    try:
        result = subprocess.run(
            ["pdfinfo", str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
        )
    except FileNotFoundError:
        return {
            "available": False,
            "ok": False,
            "error": "pdfinfo absent",
        }
    except subprocess.TimeoutExpired:
        return {
            "available": True,
            "ok": False,
            "error": "timeout pdfinfo",
        }

    if result.returncode != 0:
        return {
            "available": True,
            "ok": False,
            "error": result.stderr.strip() or "pdfinfo erreur",
        }

    info = {
        "available": True,
        "ok": True,
        "pages": "",
        "encrypted": "",
        "title": "",
        "producer": "",
    }

    for line in result.stdout.splitlines():
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()

        if key == "pages":
            info["pages"] = value
        elif key == "encrypted":
            info["encrypted"] = value
        elif key == "title":
            info["title"] = value
        elif key == "producer":
            info["producer"] = value

    return info


def check_pdf(path: Path) -> dict:
    rel = path.relative_to(MANUALS_ROOT)
    system = rel.parts[0] if len(rel.parts) > 1 else ""
    size = path.stat().st_size

    issues = []
    status = "OK"

    try:
        with path.open("rb") as file:
            head = file.read(2048)
            file.seek(max(size - 4096, 0))
            tail = file.read()
    except Exception as error:
        return {
            "system": system,
            "file": str(rel),
            "size_bytes": size,
            "size_human": human_size(size),
            "pages": "",
            "bytes_per_page": "",
            "bytes_per_page_human": "",
            "status": "ERREUR",
            "issues": f"lecture impossible: {error}",
        }

    if not head.startswith(b"%PDF"):
        if b"%PDF" in head:
            issues.append("header PDF pas au début")
        else:
            issues.append("header PDF absent")

    if b"%%EOF" not in tail:
        issues.append("EOF PDF absent")

    if size < MIN_BYTES_HARD:
        issues.append("taille minuscule")
    elif size < MIN_BYTES_WARN:
        issues.append("taille très faible")

    if size > BIG_BYTES_HARD:
        issues.append("taille énorme > 100 Mo")
    elif size > BIG_BYTES_WARN:
        issues.append("taille élevée > 50 Mo")

    info = run_pdfinfo(path)

    pages = ""
    bytes_per_page = ""
    bytes_per_page_human = ""

    if not info.get("available"):
        issues.append("pdfinfo absent")
    elif not info.get("ok"):
        issues.append(f"pdfinfo erreur: {info.get('error')}")
    else:
        pages = info.get("pages", "")

        encrypted = info.get("encrypted", "").lower()
        if encrypted.startswith("yes"):
            issues.append("PDF chiffré")

        try:
            pages_int = int(pages)

            if pages_int <= 0:
                issues.append("0 page détectée")
            else:
                bpp = size // pages_int
                bytes_per_page = str(bpp)
                bytes_per_page_human = human_size(bpp)

                if bpp > MAX_BYTES_PER_PAGE_HARD:
                    issues.append("> 10 Mo/page")
                elif bpp > MAX_BYTES_PER_PAGE_WARN:
                    issues.append("> 5 Mo/page")

                if pages_int <= 2 and size > 20 * 1024 * 1024:
                    issues.append("très gros pour peu de pages")

        except Exception:
            issues.append("nombre de pages illisible")

    if issues:
        serious = any(
            token in " | ".join(issues)
            for token in [
                "header PDF absent",
                "EOF PDF absent",
                "taille minuscule",
                "taille énorme",
                "> 10 Mo/page",
                "pdfinfo erreur",
                "PDF chiffré",
            ]
        )
        status = "A_VERIFIER" if serious else "AVERTISSEMENT"

    return {
        "system": system,
        "file": str(rel),
        "size_bytes": size,
        "size_human": human_size(size),
        "pages": pages,
        "bytes_per_page": bytes_per_page,
        "bytes_per_page_human": bytes_per_page_human,
        "status": status,
        "issues": " | ".join(issues),
    }


def read_gamelist_manuals() -> set[str]:
    manuals = set()

    if not GAMELISTS_ROOT.is_dir():
        return manuals

    for gamelist in GAMELISTS_ROOT.glob("*/gamelist.xml"):
        try:
            tree = ET.parse(gamelist)
            root = tree.getroot()
        except Exception:
            continue

        for game in root.findall("game"):
            manual = game.findtext("manual")

            if not manual:
                continue

            manual = manual.strip()

            if manual:
                manuals.add(manual)

    return manuals


def normalize_manual_path(value: str) -> Path:
    value = value.strip()

    if value.startswith("~/"):
        return HOME / value[2:]

    p = Path(value)

    if p.is_absolute():
        return p

    return p


def check_gamelist_links(pdf_files: list[Path]) -> tuple[list[dict], list[dict]]:
    linked_values = read_gamelist_manuals()

    pdf_abs = {p.resolve() for p in pdf_files}
    pdf_by_name = {p.name: p for p in pdf_files}

    linked_existing = set()
    missing_links = []

    for value in linked_values:
        p = normalize_manual_path(value)

        exists = False

        if p.is_absolute() and p.exists():
            exists = True
            linked_existing.add(p.resolve())
        elif p.name in pdf_by_name:
            exists = True
            linked_existing.add(pdf_by_name[p.name].resolve())

        if not exists:
            missing_links.append({
                "manual_entry": value,
                "status": "LIEN_MORT",
                "issues": "manuel référencé dans gamelist.xml mais fichier absent",
            })

    unlinked = []

    for p in pdf_files:
        if p.resolve() not in linked_existing:
            unlinked.append({
                "manual_entry": str(p.relative_to(MANUALS_ROOT)),
                "status": "NON_LIE",
                "issues": "PDF présent mais pas trouvé dans les gamelist.xml",
            })

    return missing_links, unlinked


def main():
    parser = argparse.ArgumentParser(
        description="Contrôle qualité des manuels PDF RetroPie"
    )

    parser.add_argument("system", nargs="?", help="Système à contrôler, ex: nes, snes")
    parser.add_argument("--root", default=str(MANUALS_ROOT), help="Dossier racine des PDF")
    parser.add_argument("--only-problems", action="store_true", help="Afficher seulement les problèmes")
    parser.add_argument("--check-gamelists", action="store_true", help="Vérifier les liens avec les gamelist.xml")
    parser.add_argument("--no-csv", action="store_true", help="Ne pas écrire le rapport CSV")

    args = parser.parse_args()

    root = Path(args.root).expanduser()

    if not root.is_dir():
        raise SystemExit(f"❌ Dossier introuvable : {root}")

    if args.system:
        scan_root = root / args.system
    else:
        scan_root = root

    if not scan_root.is_dir():
        raise SystemExit(f"❌ Système introuvable : {scan_root}")

    pdf_files = sorted(scan_root.rglob("*.pdf"))

    print()
    print("🔎 Contrôle qualité des manuels")
    print(f"📁 Dossier : {scan_root}")
    print(f"📄 PDF trouvés : {len(pdf_files)}")
    print()

    rows = []

    ok_count = 0
    warn_count = 0
    problem_count = 0

    for pdf in pdf_files:
        row = check_pdf(pdf)
        rows.append(row)

        if row["status"] == "OK":
            ok_count += 1
        elif row["status"] == "AVERTISSEMENT":
            warn_count += 1
        else:
            problem_count += 1

        if args.only_problems and row["status"] == "OK":
            continue

        icon = {
            "OK": "✅",
            "AVERTISSEMENT": "⚠️",
            "A_VERIFIER": "❌",
            "ERREUR": "💥",
        }.get(row["status"], "❓")

        pages = f"{row['pages']} pages" if row["pages"] else "pages ?"
        bpp = f", {row['bytes_per_page_human']}/page" if row["bytes_per_page_human"] else ""

        print(f"{icon} {row['file']}")
        print(f"   Taille : {row['size_human']} | {pages}{bpp}")

        if row["issues"]:
            print(f"   Notes  : {row['issues']}")

    missing_links = []
    unlinked = []

    if args.check_gamelists:
        missing_links, unlinked = check_gamelist_links(pdf_files)

        print()
        print("🔗 Vérification gamelist.xml")
        print(f"❌ Liens morts : {len(missing_links)}")
        print(f"⚠️ PDF non liés : {len(unlinked)}")

        if missing_links:
            print()
            print("Liens morts :")
            for item in missing_links[:50]:
                print(f"  ❌ {item['manual_entry']}")

        if unlinked:
            print()
            print("PDF non liés :")
            for item in unlinked[:50]:
                print(f"  ⚠️ {item['manual_entry']}")

    print()
    print("📊 Résumé")
    print(f"✅ OK             : {ok_count}")
    print(f"⚠️ Avertissements : {warn_count}")
    print(f"❌ À vérifier     : {problem_count}")

    if not args.no_csv:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)

        with REPORT_CSV.open("w", encoding="utf-8", newline="") as file:
            fieldnames = [
                "system",
                "file",
                "size_bytes",
                "size_human",
                "pages",
                "bytes_per_page",
                "bytes_per_page_human",
                "status",
                "issues",
            ]

            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        print()
        print(f"📝 Rapport écrit : {REPORT_CSV}")

    if problem_count:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

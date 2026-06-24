#!/usr/bin/env python3

from pathlib import Path
import argparse
import csv
import json
import subprocess
import sys
import time

HOME = Path.home()

ROOT = HOME / "Documents/save_retropie/Manuels"
SCRIPT_V3 = ROOT / "scripts/moissonner-manuels-v3.py"
INPUT_CSV = ROOT / "rapports/liste-jeux-pour-manuels-clean.csv"
REPORT_DIR = ROOT / "rapports"
STATE_FILE = REPORT_DIR / "moisson-v3-cute-state.json"

DEFAULT_SOURCES = "localcsv,notipix,archive"


def banner():
    print()
    print("🌾━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("   Moissonneuse V3 Cute")
    print("   Sources : localcsv → notipix → archive")
    print("🌾━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()


def load_systems() -> list[str]:
    if not INPUT_CSV.is_file():
        raise SystemExit(
            f"❌ CSV introuvable : {INPUT_CSV}\n"
            "Lance d'abord :\n"
            "  scripts/scan-gamelists-manuels.py\n"
            "  scripts/prepare-recherche-manuels.py"
        )

    systems = set()

    with INPUT_CSV.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        if "system" not in reader.fieldnames:
            raise SystemExit("❌ Colonne 'system' absente du CSV clean")

        for row in reader:
            system = (row.get("system") or "").strip()
            if system:
                systems.add(system)

    return sorted(systems)


def choose_system(systems: list[str]) -> str:
    print("🎮 Consoles disponibles :")
    print()

    for index, system in enumerate(systems, start=1):
        print(f"  {index:2d}) {system}")

    print()

    while True:
        choice = input("Choix console : ").strip()

        if not choice:
            continue

        if choice.isdigit():
            i = int(choice)

            if 1 <= i <= len(systems):
                return systems[i - 1]

        print("❌ Choix invalide")


def save_state(payload: dict) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def load_state() -> dict | None:
    if not STATE_FILE.is_file():
        return None

    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None


def clear_state() -> None:
    if STATE_FILE.is_file():
        STATE_FILE.unlink()


def run_v3(system: str, args) -> int:
    command = [
        sys.executable,
        str(SCRIPT_V3),
        system,
        "--sources",
        args.sources,
        "--sleep",
        str(args.sleep),
    ]

    if args.download:
        command.append("--download")

    if args.debug:
        command.append("--debug")

    if args.limit:
        command.extend(["--limit", str(args.limit)])

    if args.rows:
        command.extend(["--rows", str(args.rows)])

    if args.language:
        command.extend(["--language", args.language])

    if args.refresh_notipix:
        # Option réservée pour plus tard si on ajoute un cache Notipix.
        pass

    if args.refresh_replacementdocs:
        command.append("--refresh-replacementdocs")

    if args.replacementdocs_platform_id:
        command.extend(["--replacementdocs-platform-id", args.replacementdocs_platform_id])

    if args.replacementdocs_pages:
        command.extend(["--replacementdocs-pages", str(args.replacementdocs_pages)])

    print()
    print(f"🚀 Lancement : {system}")
    print("   " + " ".join(command))
    print()

    return subprocess.call(command)


def main():
    parser = argparse.ArgumentParser(
        description="Moissonneuse V3 Cute : localcsv → notipix → archive"
    )

    parser.add_argument("system", nargs="?", help="Console à traiter")
    parser.add_argument("--choose", action="store_true", help="Choisir la console dans un menu")
    parser.add_argument("--all", action="store_true", help="Traiter toutes les consoles")
    parser.add_argument("--resume", action="store_true", help="Reprendre la dernière session")
    parser.add_argument("--restart", action="store_true", help="Ignorer la reprise précédente")

    parser.add_argument("--download", action="store_true", help="Télécharger les PDF trouvés")
    parser.add_argument("--debug", action="store_true", help="Afficher les détails de recherche")
    parser.add_argument("--limit", type=int, default=0, help="Limiter le nombre de jeux par console")
    parser.add_argument("--sleep", type=float, default=4.0, help="Pause entre les requêtes")
    parser.add_argument("--rows", type=int, default=20)
    parser.add_argument("--language", choices=["fr", "en"], default="fr")

    parser.add_argument(
        "--sources",
        default=DEFAULT_SOURCES,
        help="Sources : localcsv,notipix,archive,replacementdocs"
    )

    parser.add_argument("--refresh-notipix", action="store_true")
    parser.add_argument("--refresh-replacementdocs", action="store_true")
    parser.add_argument("--replacementdocs-pages", type=int, default=2)
    parser.add_argument("--replacementdocs-platform-id", default="")

    args = parser.parse_args()

    banner()

    if not SCRIPT_V3.is_file():
        raise SystemExit(f"❌ Script V3 introuvable : {SCRIPT_V3}")

    systems = load_systems()

    if args.restart:
        clear_state()

    start_index = 0
    selected_systems = []

    if args.resume and not args.restart:
        state = load_state()

        if state:
            selected_systems = state.get("systems", [])
            start_index = int(state.get("index", 0))
            print(f"🔁 Reprise : {start_index + 1}/{len(selected_systems)}")
        else:
            print("⚠️ Aucun état de reprise trouvé")

    if not selected_systems:
        if args.all:
            selected_systems = systems
        elif args.choose:
            selected_systems = [choose_system(systems)]
        elif args.system:
            selected_systems = [args.system]
        else:
            selected_systems = [choose_system(systems)]

    if not selected_systems:
        raise SystemExit("❌ Aucune console à traiter")

    print("📦 Consoles à traiter :")
    for system in selected_systems:
        print(f"  - {system}")

    print()
    print(f"🔎 Sources : {args.sources}")
    print(f"📥 Download : {'oui' if args.download else 'dry-run'}")
    print(f"⏱️ Sleep : {args.sleep}s")
    print()

    try:
        for index in range(start_index, len(selected_systems)):
            system = selected_systems[index]

            save_state({
                "systems": selected_systems,
                "index": index,
                "current_system": system,
                "sources": args.sources,
                "download": args.download,
                "limit": args.limit,
                "sleep": args.sleep,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            })

            code = run_v3(system, args)

            if code != 0:
                print()
                print(f"❌ Arrêt sur {system} avec code {code}")
                print(f"🔁 Reprise possible avec :")
                print(f"   scripts/moissonner-manuels-v3-cute.py --resume")
                raise SystemExit(code)

            print()
            print(f"✅ Console terminée : {system}")
            print("🌿 Petite pause anti-portier web...")
            time.sleep(args.sleep)

        clear_state()
        print()
        print("🏁 Moisson V3 Cute terminée sans drame majeur.")

    except KeyboardInterrupt:
        print()
        print("🛑 Interruption demandée")
        print("🔁 Reprise possible avec :")
        print("   scripts/moissonner-manuels-v3-cute.py --resume")
        raise SystemExit(130)


if __name__ == "__main__":
    main()

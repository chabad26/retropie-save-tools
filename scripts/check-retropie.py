#!/usr/bin/env python3

from pathlib import Path
import argparse
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

HOME = Path.home()
ROOT = HOME / "Documents/save_retropie"
MANUELS = ROOT / "Manuels"
MANUELS_SCRIPTS = MANUELS / "scripts"
PDF_ROOT = MANUELS / "pdf"
REPORTS = MANUELS / "rapports"

ES_CFG = HOME / ".emulationstation/es_systems.cfg"
GAMELISTS = HOME / ".emulationstation/gamelists"

PROFILES = {
    "Switch / Eden": ROOT / "switch_profiles",
    "PS3 / RPCS3": ROOT / "ps3_profiles",
    "Xbox 360 / Xenia": ROOT / "xbox360_profiles",
}

PLAYERS = ["lucas", "nolan", "oceane", "oliv"]

REQUIRED_SCRIPTS = [
    MANUELS_SCRIPTS / "moissonner-manuels-v3.py",
    MANUELS_SCRIPTS / "moissonner-manuels-v3-cute.py",
    MANUELS_SCRIPTS / "check-manuels.py",
    MANUELS_SCRIPTS / "resume-qualite-manuels.py",
    MANUELS_SCRIPTS / "optimize-manuels.py",
    MANUELS_SCRIPTS / "manual-hotkey-watcher.py",
    MANUELS_SCRIPTS / "open-current-manual.sh",
    MANUELS_SCRIPTS / "set-current-manual.py",
    MANUELS_SCRIPTS / "show-current-manual-status.sh",
]

CUSTOM_LAUNCHERS = HOME / "RetroPie/roms/emulateurs/custom-launchers"

REQUIRED_LAUNCHERS = [
    CUSTOM_LAUNCHERS / "launch-switch-profile.sh",
    CUSTOM_LAUNCHERS / "launch-ps3-profile.sh",
    CUSTOM_LAUNCHERS / "launch-ps3-core.sh",
    CUSTOM_LAUNCHERS / "launch-xenia-profile.sh",
    CUSTOM_LAUNCHERS / "launch-xenia-canary.sh",
]

REQUIRED_COMMANDS = [
    "python3",
    "pdfinfo",
    "gs",
    "xpdf",
    "yad",
    "notify-send",
    "xdotool",
    "wine",
]


class Report:
    def __init__(self):
        self.ok = 0
        self.warn = 0
        self.err = 0
        self.fixed = 0

    def section(self, title):
        print()
        print("━" * 54)
        print(title)
        print("━" * 54)

    def good(self, msg):
        self.ok += 1
        print(f"✅ {msg}")

    def warning(self, msg):
        self.warn += 1
        print(f"⚠️ {msg}")

    def error(self, msg):
        self.err += 1
        print(f"❌ {msg}")

    def repair(self, msg):
        self.fixed += 1
        print(f"🔧 {msg}")

    def summary(self):
        print()
        print("━" * 54)
        print("📊 Résumé")
        print("━" * 54)
        print(f"✅ OK             : {self.ok}")
        print(f"⚠️ Avertissements : {self.warn}")
        print(f"❌ Erreurs        : {self.err}")
        print(f"🔧 Réparations    : {self.fixed}")
        print()

        if self.err:
            raise SystemExit(1)


def run(cmd):
    try:
        return subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=20,
        )
    except Exception as exc:
        return exc


def chmod_x(path, report, fix=False):
    if not path.exists():
        report.error(f"Absent : {path}")
        return

    if os.access(path, os.X_OK):
        report.good(f"Exécutable : {path}")
        return

    report.warning(f"Non exécutable : {path}")

    if fix:
        path.chmod(path.stat().st_mode | 0o755)
        report.repair(f"chmod +x : {path}")


def ensure_dir(path, report, fix=False):
    if path.is_dir():
        report.good(f"Dossier présent : {path}")
        return

    report.warning(f"Dossier absent : {path}")

    if fix:
        path.mkdir(parents=True, exist_ok=True)
        report.repair(f"Dossier créé : {path}")


def check_dirs(report, fix=False):
    report.section("📁 Dossiers principaux")

    for path in [
        ROOT,
        MANUELS,
        MANUELS_SCRIPTS,
        PDF_ROOT,
        REPORTS,
        MANUELS / "backups",
    ]:
        ensure_dir(path, report, fix)


def check_scripts(report, fix=False):
    report.section("📜 Scripts")

    for path in REQUIRED_SCRIPTS:
        chmod_x(path, report, fix)

    report.section("🎮 Launchers")

    for path in REQUIRED_LAUNCHERS:
        chmod_x(path, report, fix)


def check_commands(report):
    report.section("🧰 Dépendances système")

    for cmd in REQUIRED_COMMANDS:
        found = shutil.which(cmd)

        if found:
            report.good(f"{cmd} : {found}")
        else:
            report.warning(f"{cmd} absent")


def check_profiles(report, fix=False):
    report.section("👤 Profils joueurs")

    for label, base in PROFILES.items():
        print()
        print(label)

        ensure_dir(base, report, fix)

        for player in PLAYERS:
            p = base / player

            if p.is_dir():
                report.good(f"Profil présent : {label} / {player}")
            else:
                report.warning(f"Profil absent : {label} / {player}")

                if fix:
                    p.mkdir(parents=True, exist_ok=True)
                    report.repair(f"Profil créé : {p}")

        if "Switch" in label:
            for player in PLAYERS:
                for sub in ["cache", "config", "share"]:
                    ensure_dir(base / player / sub, report, fix)

        if "PS3" in label:
            for player in PLAYERS:
                for sub in ["cache", "config", "config/dev_hdd0/home"]:
                    ensure_dir(base / player / sub, report, fix)

        if "Xbox 360" in label:
            for player in PLAYERS:
                ensure_dir(base / player / "content", report, fix)


def check_symlinks(report):
    report.section("🔗 Liens actifs émulateurs")

    links = [
        HOME / ".cache/eden",
        HOME / ".config/eden",
        HOME / ".local/share/eden",
        HOME / ".config/rpcs3",
        HOME / ".cache/rpcs3",
        HOME / "Games/xenia-emu/drive_c/Xenia_Canary/content",
    ]

    for link in links:
        if link.is_symlink():
            report.good(f"Lien actif : {link} -> {link.resolve()}")
        elif link.exists():
            report.warning(f"Existe mais n'est pas un lien : {link}")
        else:
            report.warning(f"Lien absent : {link}")


def check_gamelists(report):
    report.section("🎮 Gamelists")

    if not GAMELISTS.is_dir():
        report.error(f"Dossier gamelists absent : {GAMELISTS}")
        return

    files = sorted(GAMELISTS.glob("*/gamelist.xml"))

    if not files:
        report.warning("Aucun gamelist.xml trouvé")
        return

    report.good(f"{len(files)} gamelist.xml trouvés")

    invalid = 0
    manual_links = 0
    dead_manuals = 0

    for file in files:
        try:
            tree = ET.parse(file)
            root = tree.getroot()
        except Exception as exc:
            invalid += 1
            report.error(f"XML invalide : {file} | {exc}")
            continue

        for game in root.findall("game"):
            manual = game.findtext("manual")

            if not manual:
                continue

            manual_links += 1
            p = Path(manual.strip()).expanduser()

            if not p.is_absolute():
                p = HOME / manual.strip()

            if not p.exists():
                dead_manuals += 1

    if invalid == 0:
        report.good("Tous les gamelist.xml lisibles")

    report.good(f"Balises <manual> trouvées : {manual_links}")

    if dead_manuals:
        report.error(f"Liens manuels cassés : {dead_manuals}")
    else:
        report.good("Aucun lien manuel cassé")


def check_manual_quality(report):
    report.section("📚 Qualité des manuels")

    checker = MANUELS_SCRIPTS / "check-manuels.py"

    if not checker.is_file():
        report.warning("check-manuels.py absent")
        return

    result = run([str(checker), "--only-problems", "--no-csv"])

    if isinstance(result, Exception):
        report.warning(f"Impossible de lancer check-manuels.py : {result}")
        return

    output = result.stdout + result.stderr

    if "PDF trouvés" in output:
        for line in output.splitlines():
            if "PDF trouvés" in line:
                report.good(line.strip())

    if result.returncode == 0:
        report.good("Aucun problème qualité détecté")
    else:
        report.warning("Problèmes qualité détectés")
        for line in output.splitlines():
            if line.startswith("❌") or line.startswith("⚠️"):
                print(line)


def check_services(report):
    report.section("⌨ Hotkey manuel")

    result = run(["systemctl", "is-active", "retropie-manual-hotkey.service"])

    if not isinstance(result, Exception) and result.stdout.strip() == "active":
        report.good("Service retropie-manual-hotkey actif")
    else:
        report.warning("Service retropie-manual-hotkey inactif ou absent")

    device = Path("/dev/input/by-id/usb-PowerA_NSW_wired_controller-event-joystick")

    if device.exists():
        report.good(f"Manette détectée : {device}")
    else:
        report.warning(f"Manette non détectée : {device}")


def stats(report):
    report.section("📈 Statistiques")

    pdf_count = len(list(PDF_ROOT.rglob("*.pdf"))) if PDF_ROOT.is_dir() else 0
    pdf_size = sum(p.stat().st_size for p in PDF_ROOT.rglob("*.pdf")) if PDF_ROOT.is_dir() else 0

    systems = sorted([p.name for p in PDF_ROOT.iterdir() if p.is_dir()]) if PDF_ROOT.is_dir() else []

    report.good(f"PDF : {pdf_count}")
    report.good(f"Taille manuels : {pdf_size / 1024 / 1024 / 1024:.2f} Go")
    report.good(f"Systèmes avec manuels : {len(systems)}")

    if systems:
        print("   " + ", ".join(systems[:40]))


def main():
    parser = argparse.ArgumentParser(description="Diagnostic global RetroPie Save Tools")
    parser.add_argument("--fix", action="store_true", help="Créer dossiers manquants et rendre les scripts exécutables")
    parser.add_argument("--doctor", action="store_true", help="Vérifier les dépendances système")
    parser.add_argument("--stats", action="store_true", help="Afficher les statistiques")
    parser.add_argument("--no-quality", action="store_true", help="Ne pas lancer le contrôle qualité PDF")
    args = parser.parse_args()

    report = Report()

    print()
    print("🩺 RetroPie Save Tools Doctor")

    check_dirs(report, args.fix)
    check_scripts(report, args.fix)

    if args.doctor:
        check_commands(report)

    check_profiles(report, args.fix)
    check_symlinks(report)
    check_gamelists(report)
    check_services(report)

    if not args.no_quality:
        check_manual_quality(report)

    if args.stats:
        stats(report)

    report.summary()


if __name__ == "__main__":
    main()

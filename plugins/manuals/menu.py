from pathlib import Path
import csv
import xml.etree.ElementTree as ET

from modules.core import load_settings
from modules import manuals


def get_systems():
    settings = load_settings()
    home = Path.home()
    manuals_root = Path(settings["paths"]["manuals"])
    input_csv = manuals_root / "rapports/liste-jeux-pour-manuels-clean.csv"
    es_cfg = Path(settings["paths"]["emulationstation"]) / "es_systems.cfg"

    systems = set()

    if es_cfg.is_file():
        try:
            root = ET.parse(es_cfg).getroot()
            for node in root.findall("system"):
                name = (node.findtext("name") or "").strip()
                if name:
                    systems.add(name)
        except Exception:
            pass

    if not systems and input_csv.is_file():
        with input_csv.open("r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                system = (row.get("system") or "").strip()
                if system:
                    systems.add(system)

    return sorted(systems)


def choose_system(app, title="Choisir une console", allow_all=False):
    systems = get_systems()

    if not systems:
        app.ui.msg("Erreur", "Aucune console trouvée.")
        return None

    items = []

    if allow_all:
        items.append(("__ALL__", "Toutes les consoles"))

    for system in systems:
        items.append((system, system))

    return app.ui.menu("🎮 " + title, "Consoles disponibles", items, height=28, width=78, menu_height=18)


def harvest(app):
    settings = load_settings()
    system = choose_system(app, "Moissonneuse V3", allow_all=True)

    if not system:
        return

    download = app.ui.yesno("Télécharger réellement les PDF ?")

    sleep = app.ui.input(
        "Pause",
        "Pause entre requêtes :",
        str(settings.get("manuals", {}).get("sleep", 4)),
    )

    if sleep is None:
        return

    if sleep == "":
        sleep = str(settings.get("manuals", {}).get("sleep", 4))

    app.run_action(
        manuals.harvest,
        system=None if system == "__ALL__" else system,
        all_systems=system == "__ALL__",
        download=download,
        debug=not download,
        sleep=sleep,
    )


def check(app):
    with_gamelists = app.ui.yesno("Vérifier aussi les liens gamelist.xml ?")
    app.run_action(manuals.check, with_gamelists)


def summary(app):
    app.run_action(manuals.summary)


def optimize(app):
    while True:
        choice = app.ui.menu(
            "🗜️ Optimisation PDF",
            "Compression Ghostscript avec sauvegarde automatique",
            [
                ("1", "Dry-run PDF problématiques > 50 Mo"),
                ("2", "Optimiser PDF problématiques > 50 Mo"),
                ("0", "Retour"),
            ],
        )

        if choice == "1":
            app.run_action(manuals.optimize, True)
        elif choice == "2":
            if app.ui.yesno("Confirmer optimisation réelle ?"):
                app.run_action(manuals.optimize, False)
        elif choice in ("0", None):
            return


def update_gamelists(app):
    settings = load_settings()
    manuals_root = Path(settings["paths"]["manuals"])

    system = choose_system(app, "Mise à jour gamelist", allow_all=True)

    if not system:
        return

    cmd = [manuals_root / "scripts/update-gamelists-manuals-from-pdfs.py"]

    if system != "__ALL__":
        cmd.append(system)

    app.run_cmd(cmd)


def menu(app):
    while True:
        choice = app.ui.menu(
            "📚 Manuels",
            "Gestion des manuels PDF",
            [
                ("1", "Moissonneuse V3 Cute"),
                ("2", "Contrôle qualité"),
                ("3", "Résumé qualité"),
                ("4", "Optimiser PDF lourds"),
                ("5", "Mettre à jour les gamelists"),
                ("0", "Retour"),
            ],
        )

        if choice == "1":
            harvest(app)
        elif choice == "2":
            check(app)
        elif choice == "3":
            summary(app)
        elif choice == "4":
            optimize(app)
        elif choice == "5":
            update_gamelists(app)
        elif choice in ("0", None):
            return

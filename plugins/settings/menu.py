from modules import settings
from modules.core import load_settings
from pathlib import Path


def reload(app):
    if hasattr(app, "reload_settings"):
        app.reload_settings()


def menu(app):
    while True:
        data = load_settings()

        choice = app.ui.menu(
            "⚙️ Paramètres",
            "Configuration centrale",
            [
                ("1", "Voir settings.yml"),
                ("2", "Modifier pause moissonneuse"),
                ("3", "Modifier sources manuels"),
                ("4", "Modifier seuil optimisation PDF"),
                ("0", "Retour"),
            ],
        )

        if choice == "1":
            app.ui.textbox("settings.yml", Path.home() / "Documents/save_retropie/config/settings.yml")

        elif choice == "2":
            value = app.ui.input(
                "Pause",
                "Pause entre requêtes en secondes :",
                str(data.get("manuals", {}).get("sleep", 4)),
            )
            if value is not None and value.strip().isdigit():
                settings.set_manual_sleep(value.strip())
                reload(app)
                app.ui.msg("OK", "Pause mise à jour.")

        elif choice == "3":
            value = app.ui.input(
                "Sources",
                "Sources, ex: localcsv,notipix,archive :",
                data.get("manuals", {}).get("sources", "localcsv,notipix,archive"),
            )
            if value is not None and value.strip():
                settings.set_manual_sources(value.strip())
                reload(app)
                app.ui.msg("OK", "Sources mises à jour.")

        elif choice == "4":
            value = app.ui.input(
                "Seuil",
                "Seuil optimisation, ex: 50M :",
                data.get("manuals", {}).get("quality_min_size", "50M"),
            )
            if value is not None and value.strip():
                settings.set_quality_min_size(value.strip())
                reload(app)
                app.ui.msg("OK", "Seuil mis à jour.")

        elif choice in ("0", None):
            return

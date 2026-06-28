from pathlib import Path
from modules.core import load_settings


def menu(app):
    settings = load_settings()
    manuals = Path(settings["paths"]["manuals"])

    while True:
        choice = app.ui.menu(
            "🚨 Rapports / logs",
            "Afficher les rapports utiles",
            [
                ("1", "Résumé qualité des manuels"),
                ("2", "Rapport qualité CSV"),
                ("3", "Rapport optimisation CSV"),
                ("4", "Logs ouverture manuel"),
                ("5", "Logs hotkey manuel"),
                ("6", "Logs PDF manette"),
                ("0", "Retour"),
            ],
        )

        if choice == "1":
            app.run_cmd([manuals / "scripts/resume-qualite-manuels.py", "--limit", "40"])

        elif choice == "2":
            app.ui.textbox("Rapport qualité", manuals / "rapports/rapport-qualite-manuels.csv")

        elif choice == "3":
            app.ui.textbox("Rapport optimisation", manuals / "rapports/rapport-optimisation-manuels.csv")

        elif choice == "4":
            app.ui.textbox("Logs ouverture manuel", "/tmp/retropie-open-manual.log")

        elif choice == "5":
            app.ui.textbox("Logs hotkey manuel", "/tmp/retropie-manual-hotkey.log")

        elif choice == "6":
            app.ui.textbox("Logs PDF manette", "/tmp/retropie-manual-pdf-gamepad.log")

        elif choice in ("0", None):
            return

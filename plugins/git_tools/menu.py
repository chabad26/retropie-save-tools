from pathlib import Path
from modules.core import load_settings


def root():
    return Path(load_settings()["paths"]["root"])


def menu(app):
    while True:
        choice = app.ui.menu(
            "🌿 Git / Maintenance",
            "Outils de suivi du dépôt",
            [
                ("1", "Git status"),
                ("2", "Git diff résumé"),
                ("3", "Fichiers modifiés"),
                ("4", "Voir README.md"),
                ("0", "Retour"),
            ],
        )

        if choice == "1":
            app.run_cmd(["git", "-C", str(root()), "status", "--short"])

        elif choice == "2":
            app.run_cmd(["git", "-C", str(root()), "diff", "--stat"])

        elif choice == "3":
            app.run_cmd(["git", "-C", str(root()), "ls-files", "--modified", "--others", "--exclude-standard"])

        elif choice == "4":
            app.ui.textbox("README.md", root() / "README.md")

        elif choice in ("0", None):
            return

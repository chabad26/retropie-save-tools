PLUGIN = {
    "id": "git_tools",
    "name": "🌿 Git / Maintenance",
    "description": "Status, diff, scripts modifiés et préparation commit",
    "version": "1.1.0",
    "author": "Olidev",
    "requires": ["git"],
    "order": 70,
}


def commands():
    return [
        {"id": "status", "label": "Git status"},
        {"id": "diff", "label": "Git diff résumé"},
        {"id": "files", "label": "Fichiers modifiés"},
        {"id": "readme", "label": "Voir README.md"},
    ]


def execute(app, command_id):
    from pathlib import Path
    from modules.core import load_settings

    root = Path(load_settings()["paths"]["root"])

    if command_id == "status":
        app.run_cmd(["git", "-C", str(root), "status", "--short"])

    elif command_id == "diff":
        app.run_cmd(["git", "-C", str(root), "diff", "--stat"])

    elif command_id == "files":
        app.run_cmd(["git", "-C", str(root), "ls-files", "--modified", "--others", "--exclude-standard"])

    elif command_id == "readme":
        app.ui.textbox("README.md", root / "README.md")

    else:
        app.ui.msg("Git / Maintenance", f"Commande inconnue : {command_id}")


def run(app):
    while True:
        items = [(cmd["id"], cmd["label"]) for cmd in commands()]
        items.append(("0", "Retour"))

        choice = app.ui.menu("🌿 Git / Maintenance", "Actions disponibles", items)

        if choice in ("0", None):
            return

        execute(app, choice)


def status():
    from pathlib import Path
    from modules.core import load_settings
    import subprocess

    root = Path(load_settings()["paths"]["root"])

    try:
        out = subprocess.check_output(
            ["git", "-C", str(root), "status", "--short"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception as exc:
        return {"state": "error", "title": "🌿 Git / Maintenance", "message": str(exc)}

    count = len([line for line in out.splitlines() if line.strip()])

    if count:
        return {"state": "info", "title": "🌿 Git / Maintenance", "message": f"{count} fichier(s) modifié(s)"}

    return {"state": "ok", "title": "🌿 Git / Maintenance", "message": "Dépôt propre"}


def about():
    return {
        "title": "🌿 Git / Maintenance",
        "summary": "Outils Git rapides pour suivre l’état du dépôt RetroPie Toolbox.",
    }

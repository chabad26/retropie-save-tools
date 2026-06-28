from .menu import menu

PLUGIN = {
    "id": "git_tools",
    "name": "🌿 Git / Maintenance",
    "description": "Status, diff, scripts modifiés et préparation commit",
    "version": "1.0.0",
    "author": "Olidev",
    "requires": ["git"],
    "order": 70,
}


def run(app):
    menu(app)

def status():
    from modules.core import load_settings
    from pathlib import Path
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

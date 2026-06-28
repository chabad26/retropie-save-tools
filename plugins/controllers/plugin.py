from .menu import menu

PLUGIN = {
    "id": "controllers",
    "name": "🎮 Manettes",
    "description": "Détection, test et mapping des contrôleurs",
    "version": "1.1.0",
    "author": "Olidev",
    "requires": ["python3", "udevadm"],
    "order": 30,
}


def run(app):
    menu(app)

def status():
    from modules.core import load_settings
    from pathlib import Path
    import subprocess

    manuals = Path(load_settings()["paths"]["manuals"])
    script = manuals / "scripts/controller-detect.py"

    try:
        out = subprocess.check_output([str(script)], text=True, stderr=subprocess.DEVNULL)
        count = out.count("[")
    except Exception as exc:
        return {"state": "error", "title": "🎮 Manettes", "message": str(exc)}

    if count > 0:
        return {"state": "ok", "title": "🎮 Manettes", "message": f"{count} manette(s) détectée(s)"}

    return {"state": "warning", "title": "🎮 Manettes", "message": "Aucune manette détectée"}

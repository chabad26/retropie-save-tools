PLUGIN = {
    "id": "controllers",
    "name": "🎮 Manettes",
    "description": "Détection, test et mapping des contrôleurs",
    "version": "1.2.0",
    "author": "Olidev",
    "requires": ["python3", "udevadm"],
    "order": 30,
}


def commands():
    return [
        {"id": "detect", "label": "Manettes détectées"},
        {"id": "test", "label": "Tester les touches"},
        {"id": "mapping", "label": "Voir mapping actuel"},
        {"id": "hotkey_logs", "label": "Logs hotkey manuel"},
        {"id": "pdf_logs", "label": "Logs PDF manette"},
    ]


def execute(app, command_id):
    from modules import controllers

    if command_id == "detect":
        app.run_action(controllers.detect)
    elif command_id == "test":
        app.run_action(controllers.test)
    elif command_id == "mapping":
        app.ui.textbox("Mapping contrôleur", "/home/retropie/Documents/save_retropie/Manuels/config/controller-map.json")
    elif command_id == "hotkey_logs":
        app.ui.textbox("Logs hotkey manuel", "/tmp/retropie-manual-hotkey.log")
    elif command_id == "pdf_logs":
        app.ui.textbox("Logs PDF manette", "/tmp/retropie-manual-pdf-gamepad.log")


def run(app):
    execute_menu(app)


def execute_menu(app):
    while True:
        items = [(cmd["id"], cmd["label"]) for cmd in commands()]
        items.append(("0", "Retour"))

        choice = app.ui.menu("🎮 Manettes", "Actions disponibles", items)

        if choice in ("0", None):
            return

        execute(app, choice)


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


def about():
    return {
        "title": "🎮 Manettes",
        "summary": "Détection, test et suivi des contrôleurs utilisés par RetroPie Toolbox.",
    }

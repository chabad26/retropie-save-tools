PLUGIN = {
    "id": "reports",
    "name": "🚨 Rapports / logs",
    "description": "Consulter rapports qualité, optimisation et logs",
    "version": "1.1.0",
    "author": "Olidev",
    "requires": ["python3"],
    "order": 50,
}


def commands():
    return [
        {"id": "summary", "label": "Résumé qualité des manuels"},
        {"id": "quality_csv", "label": "Rapport qualité CSV"},
        {"id": "optimize_csv", "label": "Rapport optimisation CSV"},
        {"id": "open_manual_log", "label": "Logs ouverture manuel"},
        {"id": "hotkey_log", "label": "Logs hotkey manuel"},
        {"id": "pdf_gamepad_log", "label": "Logs PDF manette"},
    ]


def execute(app, command_id):
    from pathlib import Path
    from modules.core import load_settings

    manuals = Path(load_settings()["paths"]["manuals"])

    if command_id == "summary":
        app.run_cmd([manuals / "scripts/resume-qualite-manuels.py", "--limit", "40"])
    elif command_id == "quality_csv":
        app.ui.textbox("Rapport qualité", manuals / "rapports/rapport-qualite-manuels.csv")
    elif command_id == "optimize_csv":
        app.ui.textbox("Rapport optimisation", manuals / "rapports/rapport-optimisation-manuels.csv")
    elif command_id == "open_manual_log":
        app.ui.textbox("Logs ouverture manuel", "/tmp/retropie-open-manual.log")
    elif command_id == "hotkey_log":
        app.ui.textbox("Logs hotkey manuel", "/tmp/retropie-manual-hotkey.log")
    elif command_id == "pdf_gamepad_log":
        app.ui.textbox("Logs PDF manette", "/tmp/retropie-manual-pdf-gamepad.log")
    else:
        app.ui.msg("Rapports / logs", f"Commande inconnue : {command_id}")


def run(app):
    while True:
        items = [(cmd["id"], cmd["label"]) for cmd in commands()]
        items.append(("0", "Retour"))

        choice = app.ui.menu("🚨 Rapports / logs", "Actions disponibles", items)

        if choice in ("0", None):
            return

        execute(app, choice)


def status():
    from pathlib import Path
    from modules.core import load_settings

    manuals = Path(load_settings()["paths"]["manuals"])

    paths = [
        manuals / "rapports/rapport-qualite-manuels.csv",
        manuals / "rapports/rapport-optimisation-manuels.csv",
        Path("/tmp/retropie-open-manual.log"),
        Path("/tmp/retropie-manual-hotkey.log"),
        Path("/tmp/retropie-manual-pdf-gamepad.log"),
    ]

    count = sum(1 for p in paths if p.is_file())

    return {
        "state": "ok",
        "title": "🚨 Rapports / logs",
        "message": f"{count} rapport(s)/log(s) disponible(s)",
    }


def about():
    return {
        "title": "🚨 Rapports / logs",
        "summary": "Consultation des rapports CSV et des logs générés par RetroPie Toolbox.",
    }

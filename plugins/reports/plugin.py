from .menu import menu

PLUGIN = {
    "id": "reports",
    "name": "🚨 Rapports / logs",
    "description": "Consulter rapports qualité, optimisation et logs",
    "version": "1.0.0",
    "author": "Olidev",
    "requires": ["python3"],
    "order": 50,
}


def run(app):
    menu(app)

def status():
    from modules.core import load_settings
    from pathlib import Path

    manuals = Path(load_settings()["paths"]["manuals"])
    count = 0

    for path in [
        manuals / "rapports/rapport-qualite-manuels.csv",
        manuals / "rapports/rapport-optimisation-manuels.csv",
        Path("/tmp/retropie-open-manual.log"),
        Path("/tmp/retropie-manual-hotkey.log"),
    ]:
        if path.is_file():
            count += 1

    return {"state": "ok", "title": "🚨 Rapports / logs", "message": f"{count} rapport(s)/log(s) disponible(s)"}

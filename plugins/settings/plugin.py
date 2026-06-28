from .menu import menu

PLUGIN = {
    "id": "settings",
    "name": "⚙️ Paramètres",
    "description": "Configuration centrale de RetroPie Toolbox",
    "version": "1.0.0",
    "author": "Olidev",
    "requires": ["python3"],
    "order": 60,
}


def run(app):
    menu(app)

def status():
    from modules.core import CONFIG

    if CONFIG.is_file():
        return {"state": "ok", "title": "⚙️ Paramètres", "message": "settings.yml présent"}

    return {"state": "error", "title": "⚙️ Paramètres", "message": "settings.yml absent"}

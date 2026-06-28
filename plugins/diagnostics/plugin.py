from .menu import menu

PLUGIN = {
    "id": "diagnostics",
    "name": "🩺 Diagnostic",
    "description": "Contrôle, dépendances, stats et réparation",
    "version": "1.1.0",
    "author": "Olidev",
    "requires": ["python3", "git", "pdfinfo", "gs", "xpdf", "yad", "xdotool", "wine"],
    "order": 40,
}


def run(app):
    menu(app)

def status():
    return {"state": "ok", "title": "🩺 Diagnostic", "message": "Disponible"}

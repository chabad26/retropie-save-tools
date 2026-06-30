PLUGIN = {
    "id": "diagnostics",
    "name": "🩺 Diagnostic",
    "description": "Contrôle, dépendances, stats et réparation",
    "version": "1.2.0",
    "author": "Olidev",
    "requires": ["python3"],
    "order": 40,
}


def commands():
    return [
        {"id": "quick", "label": "Diagnostic rapide"},
        {"id": "full", "label": "Diagnostic complet + dépendances + stats"},
        {"id": "fix", "label": "Réparation simple + diagnostic"},
    ]


def execute(app, command_id):
    from modules import diagnostics

    if command_id == "quick":
        app.run_action(diagnostics.quick)

    elif command_id == "full":
        app.run_action(diagnostics.full)

    elif command_id == "fix":
        if app.ui.yesno("Lancer les réparations automatiques simples ?"):
            app.run_action(diagnostics.fix)

    else:
        app.ui.msg("Diagnostic", f"Commande inconnue : {command_id}")


def run(app):
    while True:
        items = [(cmd["id"], cmd["label"]) for cmd in commands()]
        items.append(("0", "Retour"))

        choice = app.ui.menu("🩺 Diagnostic", "Actions disponibles", items)

        if choice in ("0", None):
            return

        execute(app, choice)


def status():
    return {
        "state": "ok",
        "title": "🩺 Diagnostic",
        "message": "Disponible",
    }


def about():
    return {
        "title": "🩺 Diagnostic",
        "summary": "Contrôle de l'installation RetroPie Toolbox et réparation simple.",
    }

from . import menu

PLUGIN = {
    "id": "profiles",
    "name": "👤 Profils joueurs",
    "description": "Créer, supprimer, renommer et lister les profils joueurs",
    "version": "1.3.0",
    "author": "Olidev",
    "requires": ["python3"],
    "order": 20,
}


def commands():
    return [
        {"id": "info", "label": "Afficher les infos profils"},
        {"id": "list", "label": "Lister les joueurs"},
        {"id": "create", "label": "Créer un joueur"},
        {"id": "delete", "label": "Supprimer un joueur"},
        {"id": "rename", "label": "Renommer un joueur"},
    ]


def execute(app, command_id):
    actions = {
        "info": menu.show_info,
        "list": menu.list_profiles,
        "create": menu.create_profile,
        "delete": menu.delete_profile,
        "rename": menu.rename_profile,
    }

    action = actions.get(command_id)

    if action:
        action(app)
    else:
        app.ui.msg("Profils joueurs", f"Commande inconnue : {command_id}")


def run(app):
    while True:
        items = [(cmd["id"], cmd["label"]) for cmd in commands()]
        items.append(("0", "Retour"))

        choice = app.ui.menu(
            "👤 Profils joueurs",
            "Actions disponibles",
            items,
        )

        if choice in ("0", None):
            return

        execute(app, choice)


def status():
    from modules import profiles

    players = profiles.list_players()

    if players:
        return {
            "state": "ok",
            "title": "👤 Profils joueurs",
            "message": f"{len(players)} joueur(s) : {', '.join(players)}",
        }

    return {
        "state": "warning",
        "title": "👤 Profils joueurs",
        "message": "Aucun joueur configuré",
    }


def about():
    return {
        "title": "👤 Profils joueurs",
        "summary": "Gestion centralisée des profils Switch, PS3 et Xbox 360.",
    }

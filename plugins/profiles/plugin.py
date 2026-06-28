from .menu import menu

PLUGIN = {
    "id": "profiles",
    "name": "👤 Profils joueurs",
    "description": "Créer, supprimer, renommer et lister les profils joueurs",
    "version": "1.2.0",
    "author": "Olidev",
    "requires": ["python3"],
    "order": 20,
}


def run(app):
    menu(app)

def status():
    from modules import profiles

    players = profiles.list_players()
    if players:
        return {"state": "ok", "title": "👤 Profils joueurs", "message": f"{len(players)} joueur(s) : {', '.join(players)}"}

    return {"state": "warning", "title": "👤 Profils joueurs", "message": "Aucun joueur configuré"}

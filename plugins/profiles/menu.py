from modules import profiles


def list_profiles(app):
    players = profiles.list_players()
    app.ui.msg("Joueurs", "\n".join(players) if players else "Aucun joueur.")


def show_info(app):
    app.ui.msg("👤 Profils joueurs", profiles.info_text())


def create_profile(app):
    name = app.ui.input("Créer joueur", "Nom du joueur :", "")
    if name:
        ok, msg = profiles.create_player(name)
        if hasattr(app, "reload_settings"):
            app.reload_settings()
        app.ui.msg("Résultat", msg)


def delete_profile(app):
    name = app.ui.input("Supprimer joueur", "Nom du joueur à supprimer :", "")
    if name and app.ui.yesno(
        f"Supprimer le joueur {name} ?\n\n"
        "Les dossiers seront renommés en .deleted."
    ):
        ok, msg = profiles.delete_player(name)
        if hasattr(app, "reload_settings"):
            app.reload_settings()
        app.ui.msg("Résultat", msg)


def rename_profile(app):
    old = app.ui.input("Renommer joueur", "Ancien nom :", "")
    if not old:
        return

    new = app.ui.input("Renommer joueur", "Nouveau nom :", "")
    if not new:
        return

    ok, msg = profiles.rename_player(old, new)
    if hasattr(app, "reload_settings"):
        app.reload_settings()
    app.ui.msg("Résultat", msg)


def menu(app):
    while True:
        choice = app.ui.menu(
            "👤 Profils joueurs",
            "Gestion des profils Switch, PS3 et Xbox 360",
            [
                ("info", "Afficher les infos profils"),
                ("list", "Lister les joueurs"),
                ("create", "Créer un joueur"),
                ("delete", "Supprimer un joueur"),
                ("rename", "Renommer un joueur"),
                ("0", "Retour"),
            ],
        )

        if choice == "info":
            show_info(app)
        elif choice == "list":
            list_profiles(app)
        elif choice == "create":
            create_profile(app)
        elif choice == "delete":
            delete_profile(app)
        elif choice == "rename":
            rename_profile(app)
        elif choice in ("0", None):
            return

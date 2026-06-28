from modules import profiles


def menu(app):
    while True:
        choice = app.ui.menu(
            "👤 Profils joueurs",
            "Gestion des profils Switch, PS3 et Xbox 360",
            [
                ("1", "Afficher les infos profils"),
                ("2", "Lister les joueurs"),
                ("3", "Créer un joueur"),
                ("4", "Supprimer un joueur"),
                ("5", "Renommer un joueur"),
                ("0", "Retour"),
            ],
        )

        if choice == "1":
            app.ui.msg("👤 Profils joueurs", profiles.info_text())

        elif choice == "2":
            players = profiles.list_players()
            app.ui.msg("Joueurs", "\n".join(players) if players else "Aucun joueur.")

        elif choice == "3":
            name = app.ui.input("Créer joueur", "Nom du joueur :", "")
            if name:
                ok, msg = profiles.create_player(name)
                app.reload_settings()
                app.ui.msg("Résultat", msg)

        elif choice == "4":
            name = app.ui.input("Supprimer joueur", "Nom du joueur à supprimer :", "")
            if name and app.ui.yesno(
                f"Supprimer le joueur {name} ?\n\n"
                "Les dossiers seront renommés en .deleted."
            ):
                ok, msg = profiles.delete_player(name)
                app.reload_settings()
                app.ui.msg("Résultat", msg)

        elif choice == "5":
            old = app.ui.input("Renommer joueur", "Ancien nom :", "")
            if old:
                new = app.ui.input("Renommer joueur", "Nouveau nom :", "")
                if new:
                    ok, msg = profiles.rename_player(old, new)
                    app.reload_settings()
                    app.ui.msg("Résultat", msg)

        elif choice in ("0", None):
            return

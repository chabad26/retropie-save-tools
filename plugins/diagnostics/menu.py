from modules import diagnostics


def menu(app):
    while True:
        choice = app.ui.menu(
            "🩺 Diagnostic",
            "Contrôle et réparation de l'installation",
            [
                ("1", "Diagnostic rapide"),
                ("2", "Diagnostic complet + dépendances + stats"),
                ("3", "Réparation simple + diagnostic"),
                ("0", "Retour"),
            ],
        )

        if choice == "1":
            app.run_action(diagnostics.quick)

        elif choice == "2":
            app.run_action(diagnostics.full)

        elif choice == "3":
            if app.ui.yesno("Lancer les réparations automatiques simples ?"):
                app.run_action(diagnostics.fix)

        elif choice in ("0", None):
            return

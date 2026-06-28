from modules import controllers


def menu(app):
    while True:
        choice = app.ui.menu(
            "🎮 Manettes",
            "Détection, test et mapping des contrôleurs",
            [
                ("1", "Manettes détectées"),
                ("2", "Tester les touches"),
                ("3", "Voir mapping actuel"),
                ("4", "Logs hotkey manuel"),
                ("5", "Logs PDF manette"),
                ("0", "Retour"),
            ],
        )

        if choice == "1":
            app.run_action(controllers.detect)

        elif choice == "2":
            app.run_action(controllers.test)

        elif choice == "3":
            app.ui.textbox(
                "Mapping contrôleur",
                "/home/retropie/Documents/save_retropie/Manuels/config/controller-map.json",
            )

        elif choice == "4":
            app.ui.textbox(
                "Logs hotkey manuel",
                "/tmp/retropie-manual-hotkey.log",
            )

        elif choice == "5":
            app.ui.textbox(
                "Logs PDF manette",
                "/tmp/retropie-manual-pdf-gamepad.log",
            )

        elif choice in ("0", None):
            return

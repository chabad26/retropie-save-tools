from pathlib import Path

PLUGIN = {
    "id": "settings",
    "name": "⚙️ Paramètres",
    "description": "Configuration générale de RetroPie Toolbox",
    "version": "1.1.0",
    "author": "Olidev",
    "requires": ["python3"],
    "order": 60,
}


def commands():
    return [
        {"id": "show", "label": "Voir settings.yml"},
        {"id": "sleep", "label": "Modifier pause moissonneuse"},
        {"id": "sources", "label": "Modifier ordre des sources"},
        {"id": "quality", "label": "Modifier seuil optimisation"},
    ]


def execute(app, command_id):
    from modules import settings
    from modules.core import load_settings

    data = load_settings()
    config_path = Path.home() / "Documents/save_retropie/config/settings.yml"

    if command_id == "show":
        app.ui.textbox("settings.yml", config_path)

    elif command_id == "sleep":
        value = app.ui.input(
            "Pause",
            "Pause entre requêtes en secondes :",
            str(data.get("manuals", {}).get("sleep", 4)),
        )
        if value is not None and value.strip().isdigit():
            settings.set_manual_sleep(value.strip())
            if hasattr(app, "reload_settings"):
                app.reload_settings()
            app.ui.msg("OK", "Pause mise à jour.")

    elif command_id == "sources":
        current = ",".join(data.get("manuals", {}).get("sources_order", ["notipix", "replacementdocs", "archive"]))
        value = app.ui.input(
            "Sources",
            "Ordre des sources, séparées par des virgules :",
            current,
        )
        if value is not None and value.strip():
            sources = [x.strip() for x in value.split(",") if x.strip()]
            data.setdefault("manuals", {})["sources_order"] = sources
            settings.save_settings(data)
            if hasattr(app, "reload_settings"):
                app.reload_settings()
            app.ui.msg("OK", "Ordre des sources mis à jour.")

    elif command_id == "quality":
        value = app.ui.input(
            "Seuil",
            "Seuil optimisation, ex: 50M :",
            data.get("manuals", {}).get("quality_min_size", "50M"),
        )
        if value is not None and value.strip():
            settings.set_quality_min_size(value.strip())
            if hasattr(app, "reload_settings"):
                app.reload_settings()
            app.ui.msg("OK", "Seuil mis à jour.")

    else:
        app.ui.msg("Paramètres", f"Commande inconnue : {command_id}")


def run(app):
    while True:
        items = [(cmd["id"], cmd["label"]) for cmd in commands()]
        items.append(("0", "Retour"))

        choice = app.ui.menu("⚙️ Paramètres", "Actions disponibles", items)

        if choice in ("0", None):
            return

        execute(app, choice)


def status():
    from modules.core import CONFIG

    if CONFIG.is_file():
        return {
            "state": "ok",
            "title": "⚙️ Paramètres",
            "message": "settings.yml présent",
        }

    return {
        "state": "error",
        "title": "⚙️ Paramètres",
        "message": "settings.yml absent",
    }


def about():
    return {
        "title": "⚙️ Paramètres",
        "summary": "Configuration centrale de RetroPie Toolbox.",
    }

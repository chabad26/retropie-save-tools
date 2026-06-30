PLUGIN = {
    "id": "manuals",
    "name": "📚 Manuels",
    "description": "Recherche, contrôle, optimisation et association des manuels PDF",
    "version": "1.2.0",
    "author": "Olidev",
    "requires": ["python3", "pdfinfo", "gs"],
    "order": 10,
}


def commands():
    return [
        {"id": "harvest", "label": "Moissonneuse V3 Cute"},
        {"id": "check", "label": "Contrôle qualité"},
        {"id": "summary", "label": "Résumé qualité"},
        {"id": "optimize", "label": "Optimiser PDF lourds"},
        {"id": "gamelists", "label": "Mettre à jour les gamelists"},
    ]


def execute(app, command_id):
    from . import menu as manuals_menu

    actions = {
        "harvest": manuals_menu.harvest,
        "check": manuals_menu.check,
        "summary": manuals_menu.summary,
        "optimize": manuals_menu.optimize,
        "gamelists": manuals_menu.update_gamelists,
    }

    action = actions.get(command_id)

    if action:
        action(app)
    else:
        app.ui.msg("Manuels", f"Commande inconnue : {command_id}")


def run(app):
    while True:
        items = [(cmd["id"], cmd["label"]) for cmd in commands()]
        items.append(("0", "Retour"))

        choice = app.ui.menu("📚 Manuels", "Actions disponibles", items)

        if choice in ("0", None):
            return

        execute(app, choice)


def status():
    from pathlib import Path
    import csv
    from modules.core import load_settings

    manuals = Path(load_settings()["paths"]["manuals"])
    pdf_root = manuals / "pdf"
    report = manuals / "rapports/rapport-qualite-manuels.csv"

    pdfs = list(pdf_root.rglob("*.pdf")) if pdf_root.is_dir() else []

    warning = problem = 0

    if report.is_file():
        with report.open("r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                if row.get("status") == "AVERTISSEMENT":
                    warning += 1
                elif row.get("status") in ("A_VERIFIER", "ERREUR"):
                    problem += 1

    if problem:
        return {"state": "warning", "title": "📚 Manuels", "message": f"{len(pdfs)} PDF, {problem} à vérifier"}

    if warning:
        return {"state": "info", "title": "📚 Manuels", "message": f"{len(pdfs)} PDF, {warning} avertissement(s)"}

    return {"state": "ok", "title": "📚 Manuels", "message": f"{len(pdfs)} PDF"}


def about():
    return {
        "title": "📚 Manuels",
        "summary": (
            "Gestion des manuels PDF avec ordre de priorité : "
            "Notipix, ReplacementDocs, puis Archive.org."
        ),
    }

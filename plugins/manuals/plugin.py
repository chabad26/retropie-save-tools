from .menu import menu

PLUGIN = {
    "id": "manuals",
    "name": "📚 Manuels",
    "description": "Recherche, contrôle, optimisation et association des manuels PDF",
    "version": "1.1.0",
    "author": "Olidev",
    "requires": ["python3", "pdfinfo", "gs"],
    "order": 10,
}


def run(app):
    menu(app)

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

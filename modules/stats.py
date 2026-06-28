from pathlib import Path
import csv
import xml.etree.ElementTree as ET
from .core import load_settings

def human_size(size):
    value = float(size)
    for unit in ["o", "Ko", "Mo", "Go", "To"]:
        if value < 1024 or unit == "To":
            return f"{value:.1f} {unit}" if unit != "o" else f"{int(value)} {unit}"
        value /= 1024

def collect():
    s = load_settings()
    root = Path(s["paths"]["root"])
    manuals = Path(s["paths"]["manuals"])
    pdf_root = manuals / "pdf"
    gamelists = Path(s["paths"]["emulationstation"]) / "gamelists"

    pdfs = list(pdf_root.rglob("*.pdf")) if pdf_root.is_dir() else []
    pdf_size = sum(p.stat().st_size for p in pdfs)

    systems = [p for p in pdf_root.iterdir() if p.is_dir()] if pdf_root.is_dir() else []

    games = 0
    manual_links = 0
    dead_links = 0

    if gamelists.is_dir():
        for file in gamelists.glob("*/gamelist.xml"):
            try:
                tree = ET.parse(file)
                root_xml = tree.getroot()
            except Exception:
                continue

            for game in root_xml.findall("game"):
                games += 1
                manual = game.findtext("manual")
                if manual:
                    manual_links += 1
                    p = Path(manual.strip()).expanduser()
                    if not p.exists():
                        dead_links += 1

    quality_report = manuals / "rapports/rapport-qualite-manuels.csv"
    ok = warn = problem = 0

    if quality_report.is_file():
        with quality_report.open("r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                status = row.get("status")
                if status == "OK":
                    ok += 1
                elif status == "AVERTISSEMENT":
                    warn += 1
                elif status in ("A_VERIFIER", "ERREUR"):
                    problem += 1

    profiles = 0
    for folder in ["switch_profiles", "ps3_profiles", "xbox360_profiles"]:
        p = root / folder
        if p.is_dir():
            profiles += len([x for x in p.iterdir() if x.is_dir()])

    return {
        "games": games,
        "pdfs": len(pdfs),
        "pdf_size": human_size(pdf_size),
        "systems_with_manuals": len(systems),
        "manual_links": manual_links,
        "dead_links": dead_links,
        "quality_ok": ok,
        "quality_warn": warn,
        "quality_problem": problem,
        "profiles": profiles,
    }

def dashboard_text():
    d = collect()
    return (
        "RetroPie Save Tools v2\\n\\n"
        f"Jeux détectés              : {d['games']}\\n"
        f"Manuels PDF                : {d['pdfs']}\\n"
        f"Taille des manuels         : {d['pdf_size']}\\n"
        f"Systèmes avec manuels      : {d['systems_with_manuals']}\\n\\n"
        f"Manuels liés gamelist      : {d['manual_links']}\\n"
        f"Liens cassés               : {d['dead_links']}\\n\\n"
        f"Qualité OK                 : {d['quality_ok']}\\n"
        f"Avertissements             : {d['quality_warn']}\\n"
        f"À vérifier                 : {d['quality_problem']}\\n\\n"
        f"Profils joueurs            : {d['profiles']}\\n"
    )

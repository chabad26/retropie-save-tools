#!/usr/bin/env python3

from pathlib import Path
import argparse
import csv
import shutil
import subprocess
import sys
import time

HOME = Path.home()

ROOT = HOME / "Documents/save_retropie/Manuels"
PDF_ROOT = ROOT / "pdf"
REPORT = ROOT / "rapports/rapport-qualite-manuels.csv"
BACKUP_ROOT = ROOT / "backups/pdf-avant-optimisation"
OPT_REPORT = ROOT / "rapports/rapport-optimisation-manuels.csv"


def parse_size(value: str) -> int:
    value = value.strip().lower()

    units = {
        "k": 1024,
        "kb": 1024,
        "ko": 1024,
        "m": 1024 ** 2,
        "mb": 1024 ** 2,
        "mo": 1024 ** 2,
        "g": 1024 ** 3,
        "gb": 1024 ** 3,
        "go": 1024 ** 3,
    }

    num = ""
    unit = ""

    for char in value:
        if char.isdigit() or char == ".":
            num += char
        elif not char.isspace():
            unit += char

    if not num:
        raise ValueError(f"Taille invalide : {value}")

    return int(float(num) * units.get(unit, 1))


def human_size(size: int) -> str:
    value = float(size)

    for unit in ["o", "Ko", "Mo", "Go"]:
        if value < 1024 or unit == "Go":
            if unit == "o":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024

    return f"{size} o"


def load_problem_files(min_size: int, include_warnings: bool) -> list[Path]:
    if not REPORT.is_file():
        raise SystemExit(
            f"❌ Rapport qualité introuvable : {REPORT}\n"
            "Lance d'abord : scripts/check-manuels.py --only-problems"
        )

    files = []

    with REPORT.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            status = row.get("status", "")
            size = int(row.get("size_bytes") or 0)
            rel = row.get("file", "")

            if not rel:
                continue

            if size < min_size:
                continue

            if status == "A_VERIFIER" or (include_warnings and status == "AVERTISSEMENT"):
                path = PDF_ROOT / rel

                if path.is_file():
                    files.append(path)

    return sorted(set(files))


def gs_optimize(src: Path, dst: Path, quality: str) -> tuple[bool, str]:
    settings = {
        "screen": "/screen",
        "ebook": "/ebook",
        "printer": "/printer",
        "prepress": "/prepress",
    }

    pdf_setting = settings.get(quality, "/ebook")

    command = [
        "gs",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS={pdf_setting}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        "-dDetectDuplicateImages=true",
        "-dCompressFonts=true",
        "-dSubsetFonts=true",
        f"-sOutputFile={dst}",
        str(src),
    ]

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=600,
        )
    except subprocess.TimeoutExpired:
        return False, "timeout Ghostscript"

    if result.returncode != 0:
        return False, result.stderr.strip() or "erreur Ghostscript"

    if not dst.is_file() or dst.stat().st_size <= 0:
        return False, "fichier optimisé absent ou vide"

    try:
        with dst.open("rb") as file:
            head = file.read(2048)

        if not head.startswith(b"%PDF") and b"%PDF" not in head:
            return False, "sortie non PDF"
    except Exception as error:
        return False, f"lecture sortie impossible : {error}"

    return True, ""


def optimize_one(path: Path, args) -> dict:
    before = path.stat().st_size
    rel = path.relative_to(PDF_ROOT) if path.is_relative_to(PDF_ROOT) else path.name

    tmp = path.with_suffix(path.suffix + ".optimized.tmp.pdf")

    row = {
        "file": str(rel),
        "before_bytes": before,
        "before_human": human_size(before),
        "after_bytes": "",
        "after_human": "",
        "gain_bytes": "",
        "gain_percent": "",
        "status": "",
        "message": "",
    }

    print()
    print(f"📄 {rel}")
    print(f"   Avant : {human_size(before)}")

    if args.dry_run:
        row["status"] = "DRY_RUN"
        row["message"] = "simulation"
        print("   🧪 Dry-run")
        return row

    ok, message = gs_optimize(path, tmp, args.quality)

    if not ok:
        row["status"] = "ERREUR"
        row["message"] = message
        print(f"   ❌ Erreur : {message}")
        tmp.unlink(missing_ok=True)
        return row

    after = tmp.stat().st_size
    gain = before - after
    gain_percent = (gain / before) * 100 if before else 0

    row["after_bytes"] = after
    row["after_human"] = human_size(after)
    row["gain_bytes"] = gain
    row["gain_percent"] = f"{gain_percent:.1f}"

    print(f"   Après : {human_size(after)}")
    print(f"   Gain  : {human_size(gain)} ({gain_percent:.1f}%)")

    if after >= before:
        row["status"] = "IGNORE"
        row["message"] = "pas de gain"
        print("   ⚠️ Ignoré : pas de gain")
        tmp.unlink(missing_ok=True)
        return row

    if gain_percent < args.min_gain:
        row["status"] = "IGNORE"
        row["message"] = f"gain trop faible < {args.min_gain}%"
        print(f"   ⚠️ Ignoré : gain trop faible < {args.min_gain}%")
        tmp.unlink(missing_ok=True)
        return row

    backup_path = BACKUP_ROOT / str(rel)
    backup_path.parent.mkdir(parents=True, exist_ok=True)

    if not backup_path.exists():
        shutil.copy2(path, backup_path)

    shutil.move(str(tmp), str(path))

    row["status"] = "OPTIMISE"
    row["message"] = f"backup: {backup_path}"
    print(f"   ✅ Optimisé")
    print(f"   💾 Backup : {backup_path}")

    return row


def main():
    parser = argparse.ArgumentParser(description="Optimise les manuels PDF trop lourds avec Ghostscript")

    parser.add_argument("files", nargs="*", help="PDF précis à optimiser")
    parser.add_argument("--only-problems", action="store_true", help="Utiliser rapport qualité")
    parser.add_argument("--include-warnings", action="store_true", help="Inclure les avertissements")
    parser.add_argument("--min-size", default="50M", help="Taille minimale depuis rapport qualité")
    parser.add_argument("--quality", choices=["screen", "ebook", "printer", "prepress"], default="ebook")
    parser.add_argument("--min-gain", type=float, default=10.0, help="Gain minimum en pourcentage")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0)

    args = parser.parse_args()

    targets = []

    if args.files:
        for value in args.files:
            p = Path(value).expanduser()

            if not p.is_absolute():
                p = ROOT / p

            if not p.is_file():
                print(f"⚠️ Fichier ignoré, introuvable : {p}")
                continue

            targets.append(p)

    elif args.only_problems:
        targets = load_problem_files(
            min_size=parse_size(args.min_size),
            include_warnings=args.include_warnings,
        )
    else:
        raise SystemExit(
            "❌ Donne un fichier ou utilise --only-problems\n"
            "Exemple : scripts/optimize-manuels.py 'pdf/gba/Mega Man Battle Network.pdf'"
        )

    if args.limit:
        targets = targets[:args.limit]

    print()
    print("🗜️ Optimisation PDF")
    print(f"📄 Fichiers ciblés : {len(targets)}")
    print(f"🎚️ Qualité : {args.quality}")
    print(f"📉 Gain minimum : {args.min_gain}%")
    print(f"🧪 Dry-run : {'oui' if args.dry_run else 'non'}")

    if not targets:
        print("Rien à traiter.")
        return

    rows = []

    for path in targets:
        rows.append(optimize_one(path, args))

    OPT_REPORT.parent.mkdir(parents=True, exist_ok=True)

    with OPT_REPORT.open("w", encoding="utf-8", newline="") as file:
        fieldnames = [
            "file",
            "before_bytes",
            "before_human",
            "after_bytes",
            "after_human",
            "gain_bytes",
            "gain_percent",
            "status",
            "message",
        ]

        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print()
    print(f"📝 Rapport : {OPT_REPORT}")


if __name__ == "__main__":
    main()

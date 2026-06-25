#!/usr/bin/env python3

from pathlib import Path
import argparse
import csv

HOME = Path.home()
REPORT = HOME / "Documents/save_retropie/Manuels/rapports/rapport-qualite-manuels.csv"


def human_to_bytes(value: str) -> int:
    return int(value or 0)


def print_section(title: str, rows: list[dict], limit: int) -> None:
    print()
    print(title)
    print("─" * len(title))

    if not rows:
        print("  Rien à signaler.")
        return

    for row in rows[:limit]:
        file = row["file"]
        size = row["size_human"]
        pages = row["pages"] or "?"
        bpp = row["bytes_per_page_human"] or "?"
        status = row["status"]
        issues = row["issues"]

        print(f"  {status:14} {size:>10} | {pages:>4} pages | {bpp:>10}/page | {file}")
        if issues:
            print(f"  {'':14} Notes : {issues}")


def main():
    parser = argparse.ArgumentParser(description="Résumé lisible du rapport qualité des manuels")
    parser.add_argument("--report", default=str(REPORT))
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    path = Path(args.report).expanduser()

    if not path.is_file():
        raise SystemExit(
            f"❌ Rapport introuvable : {path}\n"
            "Lance d'abord : scripts/check-manuels.py --only-problems"
        )

    with path.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))

    problems = [r for r in rows if r["status"] != "OK"]

    huge = sorted(
        [r for r in problems if int(r["size_bytes"] or 0) >= 100 * 1024 * 1024],
        key=lambda r: int(r["size_bytes"] or 0),
        reverse=True,
    )

    big = sorted(
        [r for r in problems if "taille élevée" in r["issues"]],
        key=lambda r: int(r["size_bytes"] or 0),
        reverse=True,
    )

    tiny = sorted(
        [r for r in problems if "taille minuscule" in r["issues"] or "taille très faible" in r["issues"]],
        key=lambda r: int(r["size_bytes"] or 0),
    )

    encrypted = sorted(
        [r for r in problems if "PDF chiffré" in r["issues"]],
        key=lambda r: r["file"],
    )

    heavy_per_page = sorted(
        [r for r in problems if "> 5 Mo/page" in r["issues"] or "> 10 Mo/page" in r["issues"]],
        key=lambda r: int(r["bytes_per_page"] or 0),
        reverse=True,
    )

    top_size = sorted(
        rows,
        key=lambda r: int(r["size_bytes"] or 0),
        reverse=True,
    )

    print()
    print("📊 Résumé qualité des manuels")
    print(f"📄 Total PDF       : {len(rows)}")
    print(f"✅ OK              : {sum(1 for r in rows if r['status'] == 'OK')}")
    print(f"⚠️ Avertissements  : {sum(1 for r in rows if r['status'] == 'AVERTISSEMENT')}")
    print(f"❌ À vérifier      : {sum(1 for r in rows if r['status'] == 'A_VERIFIER')}")
    print(f"💥 Erreurs         : {sum(1 for r in rows if r['status'] == 'ERREUR')}")

    print_section("🚨 PDF énormes > 100 Mo", huge, args.limit)
    print_section("⚠️ PDF lourds > 50 Mo", big, args.limit)
    print_section("🪶 PDF trop petits", tiny, args.limit)
    print_section("🔐 PDF chiffrés", encrypted, args.limit)
    print_section("🐘 PDF trop lourds par page", heavy_per_page, args.limit)
    print_section("🏋️ Top fichiers les plus lourds", top_size, args.limit)


if __name__ == "__main__":
    main()

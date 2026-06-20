#!/usr/bin/env bash
set -Eeuo pipefail

PREFIX="/home/retropie/Games/xenia-emu"
XENIA_ROOT="$PREFIX/drive_c/Xenia_Canary"
MANAGER_EXE="$XENIA_ROOT/XeniaManager.exe"
LIBRARY="$XENIA_ROOT/Config/games.json"

ROM_DIR="/home/retropie/RetroPie/roms/xbox360"
LAUNCHER_DIR="/home/retropie/RetroPie/roms/emulateurs/custom-launchers"
LAUNCHER="$LAUNCHER_DIR/launch-xenia-manager.sh"
MANIFEST="$ROM_DIR/.xenia-generated.json"

STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="/home/retropie/retropie-config-backup-$STAMP/xenia360"

echo
echo "============================================================"
echo " Bibliothèque Xbox 360 : Xenia Manager -> RetroPie"
echo "============================================================"

for command_name in python3 wine; do
    if ! command -v "$command_name" >/dev/null 2>&1; then
        echo "ERREUR : commande absente : $command_name"
        exit 1
    fi
done

if [ ! -f "$MANAGER_EXE" ]; then
    echo "ERREUR : XeniaManager.exe introuvable :"
    echo "  $MANAGER_EXE"
    exit 1
fi

if [ ! -f "$LIBRARY" ]; then
    echo "ERREUR : bibliothèque Xenia Manager introuvable :"
    echo "  $LIBRARY"
    exit 1
fi

mkdir -p "$ROM_DIR" "$LAUNCHER_DIR" "$BACKUP_DIR"

echo
echo "[1/4] Sauvegarde..."

cp -a "$LIBRARY" "$BACKUP_DIR/games.json"

if [ -f "$LAUNCHER" ]; then
    cp -a "$LAUNCHER" "$BACKUP_DIR/launch-xenia-manager.sh"
fi

if [ -f "$MANIFEST" ]; then
    cp -a "$MANIFEST" "$BACKUP_DIR/.xenia-generated.json"
fi

while IFS= read -r -d '' entry; do
    cp -a "$entry" "$BACKUP_DIR/"
done < <(
    find "$ROM_DIR" \
        -maxdepth 1 \
        -type f \
        -iname '*.xenia' \
        -print0
)

echo "Sauvegarde : $BACKUP_DIR"

echo
echo "[2/4] Création du lanceur..."

cat > "$LAUNCHER" <<'LAUNCHER_EOF'
#!/usr/bin/env bash
set -Eeuo pipefail

PREFIX="/home/retropie/Games/xenia-emu"
MANAGER_DIR="$PREFIX/drive_c/Xenia_Canary"
MANAGER_EXE="$MANAGER_DIR/XeniaManager.exe"
ENTRY="${1:-}"

die() {
    local message="$1"
    echo "ERREUR : $message" >&2

    if command -v notify-send >/dev/null 2>&1; then
        notify-send "RetroPie / Xenia Manager" "$message" || true
    fi

    exit 1
}

command -v python3 >/dev/null 2>&1 || die "Python 3 est introuvable."
command -v wine >/dev/null 2>&1 || die "Wine est introuvable."
[ -f "$MANAGER_EXE" ] || die "XeniaManager.exe est introuvable."

if [ -z "$ENTRY" ]; then
    cd "$MANAGER_DIR"

    exec env \
        WINEPREFIX="$PREFIX" \
        WINEDEBUG="-all" \
        wine "$MANAGER_EXE"
fi

[ -f "$ENTRY" ] || die "Entrée Xbox 360 introuvable : $ENTRY"

exec python3 - "$ENTRY" "$PREFIX" "$MANAGER_DIR" "$MANAGER_EXE" <<'PY'
import json
import os
import shutil
import sys
from pathlib import Path

entry = Path(sys.argv[1])
prefix = sys.argv[2]
manager_dir = sys.argv[3]
manager_exe = sys.argv[4]

try:
    with entry.open("r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)
except Exception as exc:
    raise SystemExit(f"Impossible de lire l'entrée Xenia {entry}: {exc}")

entry_type = str(payload.get("type", "game")).casefold()

if entry_type == "manager":
    manager_args = []
elif entry_type == "game":
    title = payload.get("title")

    if not isinstance(title, str) or not title:
        raise SystemExit(f"Titre de jeu absent dans {entry}")

    manager_args = [title]
else:
    raise SystemExit(f"Type d'entrée Xenia inconnu dans {entry}: {entry_type}")

wine = shutil.which("wine")

if not wine:
    raise SystemExit("Wine est introuvable.")

environment = os.environ.copy()
environment["WINEPREFIX"] = prefix
environment["WINEDEBUG"] = "-all"

os.chdir(manager_dir)

command = [wine, manager_exe, *manager_args]
os.execvpe(command[0], command, environment)
PY
LAUNCHER_EOF

chmod +x "$LAUNCHER"
echo "Lanceur : $LAUNCHER"

echo
echo "[3/4] Génération des entrées .xenia..."

python3 - "$LIBRARY" "$ROM_DIR" "$MANIFEST" <<'PY'
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

library_path = Path(sys.argv[1])
rom_dir = Path(sys.argv[2])
manifest_path = Path(sys.argv[3])
rom_dir.mkdir(parents=True, exist_ok=True)


def atomic_json_write(path: Path, payload: object) -> None:
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")

    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    temporary.replace(path)


def safe_display_filename(title: str) -> str:
    value = unicodedata.normalize("NFC", title)
    replacements = {
        "/": "／",
        "\\": "＼",
        ":": "：",
        "*": "＊",
        "?": "？",
        '"': "＂",
        "<": "＜",
        ">": "＞",
        "|": "｜",
    }

    for source, destination in replacements.items():
        value = value.replace(source, destination)

    value = "".join(" " if ord(character) < 32 else character for character in value)
    value = re.sub(r"\s+", " ", value).strip().rstrip(". ")

    if not value:
        value = "Jeu Xbox 360"

    if value.startswith("."):
        value = "_" + value[1:]

    return value


with library_path.open("r", encoding="utf-8-sig") as handle:
    raw_library = json.load(handle)

if isinstance(raw_library, list):
    games = raw_library
elif isinstance(raw_library, dict):
    games = raw_library.get("games", [])

    if not isinstance(games, list):
        raise SystemExit("Le champ 'games' de games.json n'est pas une liste.")
else:
    raise SystemExit("Structure games.json non reconnue.")

old_generated = []

if manifest_path.is_file():
    try:
        with manifest_path.open("r", encoding="utf-8-sig") as handle:
            old_manifest = json.load(handle)

        old_generated = old_manifest.get("generated_files", [])
    except Exception as exc:
        print(
            "AVERTISSEMENT : ancien manifeste illisible, "
            f"aucune suppression automatique : {exc}"
        )

for filename in old_generated:
    if not isinstance(filename, str):
        continue

    candidate = rom_dir / filename

    try:
        candidate.relative_to(rom_dir)
    except ValueError:
        continue

    if candidate.is_file() and candidate.suffix.casefold() == ".xenia":
        candidate.unlink()

manager_filename = "Xenia Manager.xenia"
atomic_json_write(
    rom_dir / manager_filename,
    {"type": "manager", "title": "Xenia Manager"},
)

used_names = {
    path.name.casefold()
    for path in rom_dir.glob("*.xenia")
    if path.name != manager_filename
}

generated = [manager_filename]
created_games = []
skipped = []
normalized_games = []

for game in games:
    if not isinstance(game, dict):
        continue

    title = game.get("title")
    game_id = str(game.get("game_id", "00000000"))
    file_locations = game.get("file_locations") or {}

    if not isinstance(title, str) or not title.strip():
        skipped.append(f"Entrée sans titre ({game_id})")
        continue

    game_path = ""

    if isinstance(file_locations, dict):
        game_path = str(file_locations.get("game", ""))

    if not game_path:
        skipped.append(f"{title} : chemin de jeu absent")
        continue

    normalized_games.append(
        (
            title.strip(),
            game_id,
            game_path,
            str(file_locations.get("config", "")),
            str(game.get("xenia_version", "")),
        )
    )

normalized_games.sort(key=lambda item: item[0].casefold())

for title, game_id, game_path, config_path, xenia_version in normalized_games:
    base_name = safe_display_filename(title)
    filename = f"{base_name}.xenia"

    if filename.casefold() in used_names:
        filename = f"{base_name} [{game_id or '00000000'}].xenia"

    counter = 2

    while filename.casefold() in used_names:
        filename = f"{base_name} [{game_id}-{counter}].xenia"
        counter += 1

    used_names.add(filename.casefold())

    payload = {
        "type": "game",
        "title": title,
        "game_id": game_id,
        "game_path": game_path,
        "config_path": config_path,
        "xenia_version": xenia_version,
    }

    atomic_json_write(rom_dir / filename, payload)
    generated.append(filename)
    created_games.append({"title": title, "file": filename, "game_id": game_id})

manifest = {
    "generated_files": generated,
    "games": created_games,
    "source": str(library_path),
}

atomic_json_write(manifest_path, manifest)

print()
print(f"Jeux générés : {len(created_games)}")

for item in created_games:
    print(f"  + {item['title']} -> {item['file']}")

if skipped:
    print()
    print(f"Entrées ignorées : {len(skipped)}")

    for message in skipped:
        print(f"  ! {message}")
PY

echo
echo "[4/4] Vérification..."

python3 - "$ROM_DIR" <<'PY'
import json
import sys
from pathlib import Path

rom_dir = Path(sys.argv[1])
entries = sorted(rom_dir.glob("*.xenia"))
errors = 0

for entry in entries:
    try:
        with entry.open("r", encoding="utf-8-sig") as handle:
            json.load(handle)
    except Exception as exc:
        errors += 1
        print(f"ERREUR : {entry.name}: {exc}")

if errors:
    raise SystemExit(1)

print(f"OK : {len(entries)} entrées valides.")
PY

echo
echo "============================================================"
echo " Terminé"
echo "============================================================"
echo
echo "Dossier Xbox 360 : $ROM_DIR"
echo "Lanceur           : $LAUNCHER"
echo "Sauvegarde        : $BACKUP_DIR"
echo
echo "Ferme puis relance EmulationStation pour actualiser la liste."

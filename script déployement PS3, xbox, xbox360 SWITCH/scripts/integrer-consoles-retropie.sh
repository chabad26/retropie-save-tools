#!/usr/bin/env bash

set -Eeuo pipefail

USER_HOME="/home/retropie"

GLOBAL_CFG="/etc/emulationstation/es_systems.cfg"
USER_CFG="$USER_HOME/.emulationstation/es_systems.cfg"

ROM_ROOT="$USER_HOME/RetroPie/roms"
LAUNCHERS="$ROM_ROOT/emulateurs/custom-launchers"

PS3_DIR="$ROM_ROOT/PS3"
SWITCH_DIR="$ROM_ROOT/Switch"
XBOX_DIR="$USER_HOME/.var/app/app.xemu.xemu/data/xemu/xemu/games"
XBOX360_DIR="$ROM_ROOT/xbox360"

RPCS3_APP="$PS3_DIR/rpcs3.AppImage"
EDEN_APP="$SWITCH_DIR/Eden.AppImage"

BACKUP_DIR="$USER_HOME/retropie-config-backup-$(date +%Y%m%d-%H%M%S)"
TMP_CFG="$(mktemp)"

cleanup() {
    rm -f "$TMP_CFG"
}

trap cleanup EXIT

echo
echo "============================================================"
echo " Intégration PS3 / Switch / Xbox / Xbox 360 dans RetroPie"
echo "============================================================"

if [ ! -f "$GLOBAL_CFG" ]; then
    echo "ERREUR : fichier absent : $GLOBAL_CFG"
    exit 1
fi

if pgrep -x emulationstation >/dev/null 2>&1; then
    echo "ERREUR : EmulationStation est encore ouvert."
    echo "Quitte RetroPie avant d'exécuter ce script."
    exit 1
fi

echo
echo "[1/6] Création des dossiers..."

mkdir -p \
    "$USER_HOME/.emulationstation" \
    "$LAUNCHERS" \
    "$PS3_DIR" \
    "$SWITCH_DIR" \
    "$XBOX_DIR" \
    "$XBOX360_DIR" \
    "$BACKUP_DIR"

echo "OK"

echo
echo "[2/6] Sauvegarde des configurations..."

cp -a "$GLOBAL_CFG" "$BACKUP_DIR/es_systems-global.cfg"

if [ -f "$USER_CFG" ]; then
    cp -a "$USER_CFG" "$BACKUP_DIR/es_systems-user.cfg"
fi

if [ -d "$USER_HOME/.emulationstation/gamelists" ]; then
    cp -a \
        "$USER_HOME/.emulationstation/gamelists" \
        "$BACKUP_DIR/gamelists"
fi

echo "Sauvegarde : $BACKUP_DIR"

echo
echo "[3/6] Création des lanceurs..."

# ------------------------------------------------------------
# RPCS3
# ------------------------------------------------------------

cat > "$LAUNCHERS/launch-ps3.sh" <<'EOF'
#!/usr/bin/env bash

set -Eeuo pipefail

RPCS3="/home/retropie/RetroPie/roms/PS3/rpcs3.AppImage"
ROM="${1:-}"

if [ ! -x "$RPCS3" ]; then
    notify-send "RetroPie" "RPCS3 AppImage introuvable ou non exécutable"
    exit 1
fi

if [ -z "$ROM" ]; then
    exec "$RPCS3"
fi

# Un fichier .ps3 est un raccourci texte contenant le chemin réel
# du jeu, du dossier ou de l'EBOOT.BIN.
case "${ROM,,}" in
    *.ps3)
        TARGET="$(
            grep -vE '^[[:space:]]*(#|$)' "$ROM" |
            head -n 1
        )"
        ;;

    *)
        TARGET="$ROM"
        ;;
esac

if [ -z "${TARGET:-}" ]; then
    notify-send "RetroPie" "Le raccourci PS3 est vide"
    exit 1
fi

if [ ! -e "$TARGET" ]; then
    notify-send "RetroPie" "Jeu PS3 introuvable : $TARGET"
    exit 1
fi

exec "$RPCS3" --no-gui --fullscreen "$TARGET"
EOF

# ------------------------------------------------------------
# Eden
# ------------------------------------------------------------

cat > "$LAUNCHERS/launch-switch.sh" <<'EOF'
#!/usr/bin/env bash

set -Eeuo pipefail

EDEN="/home/retropie/RetroPie/roms/Switch/Eden.AppImage"
ROM="${1:-}"

if [ ! -x "$EDEN" ]; then
    notify-send "RetroPie" "Eden.AppImage introuvable ou non exécutable"
    exit 1
fi

if [ -z "$ROM" ]; then
    exec "$EDEN"
fi

if [ ! -f "$ROM" ]; then
    notify-send "RetroPie" "Jeu Switch introuvable : $ROM"
    exit 1
fi

exec "$EDEN" -f -g "$ROM"
EOF

# ------------------------------------------------------------
# Xemu Flatpak
# ------------------------------------------------------------

cat > "$LAUNCHERS/launch-xbox.sh" <<'EOF'
#!/usr/bin/env bash

set -Eeuo pipefail

ROM="${1:-}"

if ! flatpak info app.xemu.xemu >/dev/null 2>&1; then
    notify-send "RetroPie" "Le Flatpak Xemu n'est pas installé"
    exit 1
fi

if [ -z "$ROM" ]; then
    exec flatpak run app.xemu.xemu
fi

if [ ! -f "$ROM" ]; then
    notify-send "RetroPie" "Image Xbox introuvable : $ROM"
    exit 1
fi

exec flatpak run app.xemu.xemu \
    -full-screen \
    -dvd_path "$ROM"
EOF

# ------------------------------------------------------------
# Xenia Manager via Lutris
# ------------------------------------------------------------

cat > "$LAUNCHERS/launch-xenia-manager.sh" <<'EOF'
#!/usr/bin/env bash

set -Eeuo pipefail

if ! command -v lutris >/dev/null 2>&1; then
    notify-send "RetroPie" "Lutris est introuvable"
    exit 1
fi

GAME_ID="$(
    lutris \
        --list-games \
        --installed \
        --json 2>/dev/null |
    python3 -c '
import json
import sys

try:
    games = json.load(sys.stdin)
except Exception:
    sys.exit(1)

for game in games:
    name = str(game.get("name", "")).lower()
    slug = str(game.get("slug", "")).lower()

    if "xenia" in name or "xenia" in slug:
        game_id = game.get("id")

        if game_id is not None:
            print(game_id)
            sys.exit(0)

sys.exit(1)
' 2>/dev/null || true
)"

if [ -z "$GAME_ID" ]; then
    notify-send \
        "RetroPie" \
        "Impossible de trouver l'entrée Xenia dans Lutris"

    echo "Entrées Lutris disponibles :"
    lutris --list-games --installed
    exit 1
fi

exec lutris "lutris:rungameid/$GAME_ID"
EOF

chmod +x \
    "$LAUNCHERS/launch-ps3.sh" \
    "$LAUNCHERS/launch-switch.sh" \
    "$LAUNCHERS/launch-xbox.sh" \
    "$LAUNCHERS/launch-xenia-manager.sh"

chmod +x "$RPCS3_APP" "$EDEN_APP" 2>/dev/null || true

echo "OK"

echo
echo "[4/6] Création de l'entrée Xenia Manager..."

# Ce fichier sert uniquement à faire apparaître Xbox 360 dans
# EmulationStation. Le lanceur ouvre ensuite Xenia Manager.
touch "$XBOX360_DIR/Xenia Manager.xenia"

echo "OK"

echo
echo "[5/6] Fusion du fichier es_systems.cfg..."

python3 - \
    "$GLOBAL_CFG" \
    "$TMP_CFG" \
    "$PS3_DIR" \
    "$SWITCH_DIR" \
    "$XBOX_DIR" \
    "$XBOX360_DIR" \
    "$LAUNCHERS" <<'PY'
import copy
import sys
import xml.etree.ElementTree as ET

(
    source_path,
    destination_path,
    ps3_dir,
    switch_dir,
    xbox_dir,
    xbox360_dir,
    launchers_dir,
) = sys.argv[1:]

tree = ET.parse(source_path)
root = tree.getroot()

if root.tag != "systemList":
    raise RuntimeError(
        f"Racine XML inattendue : {root.tag}, attendu : systemList"
    )

custom_names = {
    "ps3",
    "switch",
    "xbox",
    "xbox360",
}

# Retire uniquement d'anciennes versions de NOS systèmes personnalisés.
# Toutes les autres consoles RetroPie restent intactes.
for system in list(root.findall("system")):
    name = system.findtext("name", default="").strip().lower()

    if name in custom_names:
        root.remove(system)


def add_system(
    *,
    name,
    fullname,
    path,
    extensions,
    command,
    platform,
    theme,
):
    system = ET.SubElement(root, "system")

    fields = {
        "name": name,
        "fullname": fullname,
        "path": path,
        "extension": extensions,
        "command": command,
        "platform": platform,
        "theme": theme,
    }

    for tag, value in fields.items():
        node = ET.SubElement(system, tag)
        node.text = value


add_system(
    name="ps3",
    fullname="Sony PlayStation 3",
    path=ps3_dir,
    extensions=".iso .ISO .ps3 .PS3",
    command=f"{launchers_dir}/launch-ps3.sh %ROM%",
    platform="ps3",
    theme="ps3",
)

add_system(
    name="switch",
    fullname="Nintendo Switch",
    path=switch_dir,
    extensions=".xci .XCI .nsp .NSP .nca .NCA",
    command=f"{launchers_dir}/launch-switch.sh %ROM%",
    platform="switch",
    theme="switch",
)

add_system(
    name="xbox",
    fullname="Microsoft Xbox",
    path=xbox_dir,
    extensions=".iso .ISO .xiso .XISO",
    command=f"{launchers_dir}/launch-xbox.sh %ROM%",
    platform="xbox",
    theme="xbox",
)

add_system(
    name="xbox360",
    fullname="Microsoft Xbox 360",
    path=xbox360_dir,
    extensions=".xenia .XENIA",
    command=f"{launchers_dir}/launch-xenia-manager.sh %ROM%",
    platform="xbox360",
    theme="xbox360",
)

try:
    ET.indent(tree, space="  ")
except AttributeError:
    pass

tree.write(
    destination_path,
    encoding="utf-8",
    xml_declaration=True,
)
PY

# Validation avant installation
python3 -c '
import sys
import xml.etree.ElementTree as ET

ET.parse(sys.argv[1])
print("XML valide")
' "$TMP_CFG"

cp -a "$TMP_CFG" "$USER_CFG"

echo "OK : $USER_CFG"

echo
echo "[6/6] Résultat..."

echo
echo "Systèmes personnalisés présents :"

grep -oP '(?<=<name>)(ps3|switch|xbox|xbox360)(?=</name>)' \
    "$USER_CFG" || true

echo
echo "Configuration terminée."
echo "Redémarre maintenant EmulationStation."
echo
echo "Sauvegarde disponible ici :"
echo "$BACKUP_DIR"

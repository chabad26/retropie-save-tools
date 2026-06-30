#!/usr/bin/env bash

set -Eeuo pipefail

GAMES_DIR="${1:-/home/retropie/RetroPie/roms/PS3/JEUX}"
SHORTCUT_DIR="${2:-/home/retropie/RetroPie/roms/PS3}"
FORCE="${FORCE:-0}"

created=0
skipped=0
not_found=0
errors=0
iso_links=0

echo
echo "============================================================"
echo " Génération des raccourcis PS3 pour RetroPie"
echo "============================================================"
echo
echo "Jeux source       : $GAMES_DIR"
echo "Raccourcis créés  : $SHORTCUT_DIR"
echo

if [ ! -d "$GAMES_DIR" ]; then
    echo "❌ Dossier introuvable : $GAMES_DIR"
    exit 1
fi

mkdir -p "$SHORTCUT_DIR"

echo "🎮 Création des liens ISO..."
find "$SHORTCUT_DIR" -maxdepth 1 -type l -iname "*.iso" -delete

while IFS= read -r -d '' iso; do
    link="$SHORTCUT_DIR/$(basename "$iso")"

    if ln -sf "$iso" "$link"; then
        echo "✅ ISO : $(basename "$iso")"
        ((iso_links += 1))
    else
        echo "❌ ISO impossible : $iso"
        ((errors += 1))
    fi
done < <(
    find "$GAMES_DIR" \
        -maxdepth 1 \
        -type f \
        -iname "*.iso" \
        -print0 |
    sort -z
)

echo
echo "🎮 Création des raccourcis .PS3 depuis dossiers..."

while IFS= read -r -d '' game_dir; do
    game_name="$(basename "$game_dir")"
    shortcut="$SHORTCUT_DIR/$game_name.PS3"
    eboot=""

    candidates=(
        "$game_dir/PS3_GAME/USRDIR/EBOOT.BIN"
        "$game_dir/USRDIR/EBOOT.BIN"
        "$game_dir/EBOOT.BIN"
    )

    for candidate in "${candidates[@]}"; do
        if [ -f "$candidate" ]; then
            eboot="$candidate"
            break
        fi
    done

    if [ -z "$eboot" ]; then
        while IFS= read -r -d '' candidate; do
            eboot="$candidate"
            break
        done < <(
            find "$game_dir" \
                -type f \
                -iname 'EBOOT.BIN' \
                -print0 2>/dev/null
        )
    fi

    if [ -z "$eboot" ]; then
        echo "⚠️ Aucun EBOOT.BIN trouvé : $game_name"
        ((not_found += 1))
        continue
    fi

    if [ -e "$shortcut" ] && [ "$FORCE" != "1" ]; then
        echo "⏭️ Déjà présent : $(basename "$shortcut")"
        ((skipped += 1))
        continue
    fi

    temp_file="$shortcut.tmp.$$"

    if ! printf '%s\n' "$eboot" > "$temp_file"; then
        echo "❌ Impossible de créer : $shortcut"
        rm -f "$temp_file"
        ((errors += 1))
        continue
    fi

    if ! mv -f "$temp_file" "$shortcut"; then
        echo "❌ Impossible d'installer : $shortcut"
        rm -f "$temp_file"
        ((errors += 1))
        continue
    fi

    echo "✅ Dossier : $game_name"
    echo "   → $eboot"

    ((created += 1))

done < <(
    find "$GAMES_DIR" \
        -mindepth 1 \
        -maxdepth 1 \
        -type d \
        -print0 |
    sort -z
)

echo
echo "============================================================"
echo " Résultat"
echo "============================================================"
echo "Liens ISO créés   : $iso_links"
echo "Raccourcis .PS3   : $created"
echo "Déjà présents     : $skipped"
echo "EBOOT.BIN absents : $not_found"
echo "Erreurs           : $errors"
echo

if [ "$iso_links" -gt 0 ] || [ "$created" -gt 0 ]; then
    echo "✅ PS3 synchronisée pour RetroPie."
else
    echo "ℹ️ Aucun nouveau raccourci ou lien ISO créé."
fi

#!/usr/bin/env bash

set -Eeuo pipefail

# Dossier contenant les dossiers de jeux PS3.
# Il peut aussi être fourni en premier argument.
GAMES_DIR="${1:-/home/retropie/RetroPie/roms/PS3/JEUX}"

# Dossier où seront créés les fichiers .PS3.
# Il peut être fourni en second argument.
SHORTCUT_DIR="${2:-/home/retropie/RetroPie/roms/PS3}"

# FORCE=1 permet de remplacer les raccourcis existants.
FORCE="${FORCE:-0}"

created=0
skipped=0
not_found=0
errors=0

echo
echo "============================================================"
echo " Génération des raccourcis PS3 pour RetroPie"
echo "============================================================"
echo
echo "Dossiers des jeux : $GAMES_DIR"
echo "Raccourcis créés : $SHORTCUT_DIR"
echo

if [ ! -d "$GAMES_DIR" ]; then
    echo "❌ Dossier introuvable : $GAMES_DIR"
    exit 1
fi

mkdir -p "$SHORTCUT_DIR"

# -print0 protège les noms avec espaces, accents, apostrophes,
# retours à la ligne et autres caractères spéciaux.
while IFS= read -r -d '' game_dir; do
    game_name="$(basename "$game_dir")"
    shortcut="$SHORTCUT_DIR/$game_name.PS3"
    eboot=""

    # Emplacements les plus fréquents.
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

    # Recherche plus large si la structure est différente.
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

    # Écriture temporaire puis remplacement atomique.
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

    echo "✅ $game_name"
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
echo "Créés             : $created"
echo "Déjà présents     : $skipped"
echo "EBOOT.BIN absents : $not_found"
echo "Erreurs           : $errors"
echo

if [ "$created" -gt 0 ]; then
    echo "✅ Les raccourcis PS3 ont été générés."
else
    echo "ℹ️ Aucun nouveau raccourci n'a été créé."
fi

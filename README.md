# RetroPie Toolbox

Scripts personnels pour sauvegarder, réinstaller et enrichir une installation RetroPie / EmulationStation.

Ce dépôt contient principalement :

* des scripts de gestion de manuels PDF pour RetroPie ;
* une moissonneuse de manuels depuis Archive.org ;
* un système d’ouverture de manuel en jeu avec une touche de manette ;
* un sélecteur de profils Switch pour Eden ;
* une intégration Xenia Canary directe pour Xbox 360 ;
* des scripts de déploiement pour consoles personnalisées ;
* des scripts de génération de raccourcis et de marquees ;
* une organisation pensée pour survivre à une réinstallation propre.

> Ce dépôt ne contient pas de ROMs, BIOS, jeux, manuels PDF téléchargés, fichiers de licence, clés, firmwares, profils, sauvegardes personnelles ou contenus protégés.
> Il fournit uniquement des scripts et de la documentation.

---

## Objectif du projet

Le but est de centraliser les scripts utiles à une configuration RetroPie personnalisée :

1. intégrer des consoles supplémentaires dans EmulationStation ;
2. générer des raccourcis pour certains émulateurs ;
3. générer des éléments visuels comme les marquees ;
4. rechercher des manuels PDF de jeux ;
5. mettre à jour les `gamelist.xml` pour associer les manuels aux jeux ;
6. ouvrir les manuels en jeu via un bouton de manette ;
7. gérer des profils séparés pour certains émulateurs ;
8. faciliter la restauration après formatage ou changement de machine.

---

## Système testé

Configuration utilisée pendant le développement :

```text
Utilisateur : retropie
Dossier ROMs : /home/retropie/RetroPie/roms
Dossier EmulationStation : /home/retropie/.emulationstation
Dossier de travail : /home/retropie/Documents/save_retropie
```

Système :

```text
Ubuntu
RetroPie
EmulationStation
Python 3
X11
Manette PowerA NSW wired controller
```

---

## Installation des dépendances

### Dépendances générales

```bash
sudo apt update
sudo apt install -y git python3 rsync
```

### Dépendances manuels et interface

```bash
sudo apt install -y python3-evdev xpdf yad x11-utils wmctrl xdotool poppler-utils
```

Rôle des paquets :

```text
python3-evdev : lecture des boutons de manette
xpdf          : affichage des PDF en plein écran
yad           : menus et messages lisibles sur TV
x11-utils     : outils X11 utiles
wmctrl        : gestion de fenêtres
xdotool       : simulation de touches pour menus à la manette
poppler-utils : diagnostic PDF avec pdfinfo
```

---

## Arborescence recommandée

```text
/home/retropie/Documents/save_retropie/
├── Manuels/
│   ├── scripts/
│   │   ├── download-manuels-valides.py
│   │   ├── manual-hotkey-watcher.py
│   │   ├── moissonner-manuels-archive-v2-cute.py
│   │   ├── moissonner-manuels-archive-v2.py
│   │   ├── moissonner-manuels-archive-v2-stable.py
│   │   ├── moissonner-manuels-v3.py
│   │   ├── open-current-manual.sh
│   │   ├── prepare-recherche-manuels.py
│   │   ├── scan-gamelists-manuels.py
│   │   ├── set-current-manual.py
│   │   └── update-gamelists-manuals-from-pdfs.py
│   ├── pdf/
│   ├── rapports/
│   └── backups/
│
├── switch_profiles/
│   ├── _common/
│   ├── lucas/
│   ├── oliv/
│   ├── nolan/
│   └── oceane/
│
└── script déployement PS3, xbox, xbox360 SWITCH/
    ├── scripts/
    └── backups/
```

Les dossiers `pdf`, `rapports`, `backups`, `switch_profiles`, ROMs, BIOS, saves et profils ne doivent pas être versionnés.

---

## `.gitignore` conseillé

```gitignore
# Gros dossiers locaux / backups RetroPie
/retropie-carbon-final-*/
/overlays_retropie/

# Manuels : on garde uniquement les scripts
/Manuels/*
!/Manuels/scripts/
!/Manuels/scripts/**

# Backups locaux
Manuels/backups/
*.bak*
*.OK-*

# Rapports / caches / états locaux
Manuels/rapports/
*.csv
__pycache__/
*.pyc
moisson-state.json

# Manuels téléchargés
*.pdf

# Profils, saves et fichiers privés
switch_profiles/
saves_xenia/
*.keys
prod.keys
title.keys
*.pem

# ROMs / BIOS / contenus protégés
roms/
ROMs/
bios/
BIOS/
*.iso
*.chd
*.cue
*.bin
*.rom
*.rvz
*.wbfs
*.xci
*.nsp
*.nro
*.pkg
*.rap
*.zip
*.7z
*.rar

# Système / fichiers temporaires
.DS_Store
Thumbs.db
*.log
*.tmp
*.swp
*~
```

---

# Partie 1 : manuels RetroPie

## Organisation des manuels

Le dossier réel des manuels est :

```text
/home/retropie/Documents/save_retropie/Manuels/pdf
```

Il est exposé à RetroPie via un lien symbolique :

```bash
ln -s /home/retropie/Documents/save_retropie/Manuels/pdf \
      /home/retropie/RetroPie/manuals
```

Vérification :

```bash
ls -l /home/retropie/RetroPie/manuals
```

Résultat attendu :

```text
/home/retropie/RetroPie/manuals -> /home/retropie/Documents/save_retropie/Manuels/pdf
```

---

## Ordre d’exécution recommandé

### 1. Scanner les gamelists

```bash
cd /home/retropie/Documents/save_retropie/Manuels
scripts/scan-gamelists-manuels.py
```

Résultat attendu :

```text
liste-jeux-pour-manuels.csv
```

---

### 2. Nettoyer les noms de jeux

```bash
scripts/prepare-recherche-manuels.py
```

Résultat attendu :

```text
liste-jeux-pour-manuels-clean.csv
```

---

### 3. Tester la recherche de manuels

```bash
scripts/moissonner-manuels-archive-v2-cute.py snes --limit 20 --debug
```

Options utiles :

```text
--limit 20       limite le nombre de jeux testés
--debug          affiche les candidats trouvés
--language fr    cherche en priorité en français
--download       télécharge réellement les PDF
--choose         propose une console au démarrage
--all            traite toutes les consoles
--resume         reprend une session interrompue
--restart        ignore la session précédente
--sleep 8        ralentit les requêtes
```

---

### 4. Télécharger pour une console

```bash
scripts/moissonner-manuels-archive-v2-cute.py snes --download --sleep 8
```

---

### 5. Télécharger avec choix interactif

```bash
scripts/moissonner-manuels-archive-v2-cute.py --choose --download --sleep 8
```

---

### 6. Traiter toutes les consoles

À utiliser avec prudence :

```bash
scripts/moissonner-manuels-archive-v2-cute.py --all --download --sleep 8
```

Archive.org peut bloquer temporairement si trop de fichiers sont téléchargés rapidement. Il est recommandé de traiter une console à la fois avec `--sleep 8` ou plus.

---

## Reprise et arrêt propre

La version `cute` sauvegarde sa progression.

En cas de `Ctrl+C`, le script :

1. termine le jeu en cours ;
2. sauvegarde la position ;
3. quitte proprement.

La progression est enregistrée dans :

```text
Manuels/rapports/moisson-state.json
```

Pour reprendre :

```bash
scripts/moissonner-manuels-archive-v2-cute.py snes --resume --download --sleep 8
```

---

## Gestion des jeux multi-disques

La moissonneuse nettoie les noms de jeux multi-disques.

Exemple :

```text
Shenmue (Disc 1)
Shenmue (Disc 2)
Shenmue (Disc 3)
```

devient :

```text
Shenmue
```

Le manuel trouvé est alors lié aux différents disques du même jeu.

---

## Filtrage des faux positifs

La moissonneuse essaye d’éviter certains pièges :

```text
guides au lieu de manuels
magazines
romans
comics
PDFDrive
fichiers OPS
manuels coréens si recherche FR/EN
manuels portugais/brésiliens non souhaités
```

Exemples de rejets :

```text
Sonic_The_Hedgehog_2_1992_Kr.pdf
Chuck Rock Portuguese
Jurassic Park OPS
Jurassic Park Michael Crichton
```

Si aucun manuel correct n’est trouvé, il vaut mieux ne rien associer plutôt que d’ajouter un mauvais PDF.

---

## Mise à jour des gamelists

Quand un manuel est téléchargé, le script peut ajouter une balise :

```xml
<manual>/home/retropie/RetroPie/manuals/snes/Nom du jeu.pdf</manual>
```

dans :

```text
/home/retropie/.emulationstation/gamelists/<system>/gamelist.xml
```

---

## Réparer les gamelists depuis les PDF existants

Si des PDF existent déjà mais que les gamelists ne contiennent pas encore les balises `<manual>` :

```bash
cd /home/retropie/Documents/save_retropie/Manuels
scripts/update-gamelists-manuals-from-pdfs.py
```

---

# Partie 2 : ouverture des manuels en jeu

## Principe

Le système repose sur trois scripts :

```text
set-current-manual.py      : détecte le manuel du jeu lancé
manual-hotkey-watcher.py   : écoute un bouton de manette
open-current-manual.sh     : ouvre le PDF ou affiche un message
```

Flux :

```text
1. Un jeu se lance.
2. runcommand-onstart.sh enregistre le manuel courant dans /tmp.
3. Le watcher écoute L3.
4. Un appui long sur L3 ouvre le manuel en plein écran.
5. Si aucun manuel n’est trouvé, un message lisible s’affiche.
```

---

## Détection du bouton de manette

Avec la manette PowerA NSW wired controller :

```text
L3 = BTN_SELECT
R3 = BTN_START
```

Le choix retenu est donc :

```text
Appui long sur L3
```

Chemin stable utilisé :

```text
/dev/input/by-id/usb-PowerA_NSW_wired_controller-event-joystick
```

Vérifier :

```bash
ls -l /dev/input/by-id/
```

---

## Service systemd du bouton manuel

Créer le service :

```bash
sudo tee /etc/systemd/system/retropie-manual-hotkey.service >/dev/null <<'EOF'
[Unit]
Description=RetroPie manual hotkey watcher
After=multi-user.target

[Service]
Type=simple
User=retropie
Group=input
ExecStart=/home/retropie/Documents/save_retropie/Manuels/scripts/manual-hotkey-watcher.py /dev/input/by-id/usb-PowerA_NSW_wired_controller-event-joystick
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
EOF
```

Activer :

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now retropie-manual-hotkey.service
```

Vérifier :

```bash
systemctl status retropie-manual-hotkey.service --no-pager
journalctl -u retropie-manual-hotkey.service -f
```

---

## Droits d’accès à la manette

Si le service ne peut pas lire `/dev/input` :

```bash
sudo usermod -aG input retropie
sudo reboot
```

---

## Déclaration du manuel courant au lancement d’un jeu

Ajouter dans :

```text
/opt/retropie/configs/all/runcommand-onstart.sh
```

le bloc :

```bash
python3 "/home/retropie/Documents/save_retropie/Manuels/scripts/set-current-manual.py" "$1" "$3"
```

Rendre exécutable :

```bash
sudo chmod +x /opt/retropie/configs/all/runcommand-onstart.sh
```

---

## Affichage du manuel

Le script utilise `xpdf` en plein écran.

Dans la configuration testée, la session graphique utile est :

```text
DISPLAY=:1
```

Test manuel :

```bash
DISPLAY=:1 XAUTHORITY=/home/retropie/.Xauthority \
xpdf -fullscreen "/home/retropie/RetroPie/manuals/mastersystem/Chuck Rock.pdf"
```

---

## Message si aucun manuel n’est disponible

Si aucun manuel n’est trouvé, `open-current-manual.sh` affiche un message TV lisible avec `yad` :

```text
Aucun manuel disponible
```

Test :

```bash
DISPLAY=:1 XAUTHORITY=/home/retropie/.Xauthority \
yad --center --on-top --no-buttons --timeout=2 \
    --width=720 --height=180 \
    --text="<span font='32' weight='bold'>Aucun manuel disponible</span>"
```

---

## Logs utiles pour les manuels

```text
/tmp/retropie-current-manual.txt
/tmp/retropie-current-manual.log
/tmp/retropie-manual-hotkey.log
/tmp/retropie-open-manual.log
/tmp/retropie-pdf-viewer.log
/tmp/retropie-no-manual.log
```

Commandes :

```bash
cat /tmp/retropie-current-manual.txt
cat /tmp/retropie-current-manual.log
tail -f /tmp/retropie-manual-hotkey.log /tmp/retropie-open-manual.log /tmp/retropie-pdf-viewer.log
```

---

# Partie 3 : Switch / Eden avec profils

## Objectif

Permettre de choisir un profil avant de lancer un jeu Switch.

Profils utilisés :

```text
Lucas
Oliv
Nolan
Océane
```

Dossiers Linux utilisés :

```text
lucas
oliv
nolan
oceane
```

---

## Dossiers Eden détectés

Eden utilise :

```text
/home/retropie/.cache/eden
/home/retropie/.config/eden
/home/retropie/.local/share/eden
```

Ces trois dossiers sont basculés vers le profil choisi.

---

## Arborescence des profils Switch

```text
/home/retropie/Documents/save_retropie/switch_profiles/
├── _common/
│   └── share/
│       └── keys/
├── lucas/
│   ├── cache/
│   ├── config/
│   └── share/
├── oliv/
│   ├── cache/
│   ├── config/
│   └── share/
├── nolan/
│   ├── cache/
│   ├── config/
│   └── share/
└── oceane/
    ├── cache/
    ├── config/
    └── share/
```

---

## Créer les profils

```bash
PROFILES="/home/retropie/Documents/save_retropie/switch_profiles"

for p in lucas oliv nolan oceane; do
  mkdir -p "$PROFILES/$p/cache" "$PROFILES/$p/config" "$PROFILES/$p/share"
done

mkdir -p "$PROFILES/_common/share/keys"
```

---

## Copier la config de base depuis le profil principal

Exemple : copier la config `oliv` vers les autres profils.

```bash
PROFILES="/home/retropie/Documents/save_retropie/switch_profiles"

rsync -a "$PROFILES/oliv/config/" "$PROFILES/lucas/config/"
rsync -a "$PROFILES/oliv/config/" "$PROFILES/nolan/config/"
rsync -a "$PROFILES/oliv/config/" "$PROFILES/oceane/config/"

rsync -a "$PROFILES/oliv/cache/" "$PROFILES/lucas/cache/"
rsync -a "$PROFILES/oliv/cache/" "$PROFILES/nolan/cache/"
rsync -a "$PROFILES/oliv/cache/" "$PROFILES/oceane/cache/"
```

Les dossiers `share` restent séparés pour conserver des sauvegardes distinctes.

---

## Fichiers communs Eden

Les fichiers communs ne doivent pas être publiés.

Ils peuvent être partagés localement entre profils via :

```text
/home/retropie/Documents/save_retropie/switch_profiles/_common/share/keys
```

Puis reliés à chaque profil :

```bash
PROFILES="/home/retropie/Documents/save_retropie/switch_profiles"

for p in lucas oliv nolan oceane; do
  mkdir -p "$PROFILES/$p/share"

  rm -rf "$PROFILES/$p/share/keys"
  ln -s "$PROFILES/_common/share/keys" "$PROFILES/$p/share/keys"
done
```

---

## Attention au retour YAD

Selon la configuration, `yad` peut renvoyer un profil avec un pipe final :

```text
oliv|
```

Le launcher doit nettoyer le nom avec :

```bash
PROFILE_NAME="${PROFILE_NAME%%|*}"
PROFILE_NAME="$(echo "$PROFILE_NAME" | tr -d '[:space:]')"
```

Sans ce nettoyage, Eden créera des dossiers invalides comme :

```text
switch_profiles/oliv|/cache
switch_profiles/oliv|/config
switch_profiles/oliv|/share
```

---

## Vérifier le profil actif

Après avoir choisi un profil :

```bash
ls -l /home/retropie/.cache/eden
ls -l /home/retropie/.config/eden
ls -l /home/retropie/.local/share/eden
```

Exemple attendu :

```text
/home/retropie/.cache/eden -> /home/retropie/Documents/save_retropie/switch_profiles/oceane/cache
/home/retropie/.config/eden -> /home/retropie/Documents/save_retropie/switch_profiles/oceane/config
/home/retropie/.local/share/eden -> /home/retropie/Documents/save_retropie/switch_profiles/oceane/share
```

---

## Launcher Switch avec choix du profil

Le launcher principal :

```text
/home/retropie/RetroPie/roms/emulateurs/custom-launchers/launch-switch-profile.sh
```

Il fait :

```text
1. ouvre un menu YAD stylisé ;
2. permet de choisir Lucas, Oliv, Nolan ou Océane ;
3. bascule les liens Eden vers le profil choisi ;
4. lance Eden.AppImage avec le jeu demandé.
```

---

## Support manette dans le menu Switch

Le script suivant traduit les boutons de manette en touches clavier pour contrôler le menu YAD :

```text
/home/retropie/RetroPie/roms/emulateurs/custom-launchers/switch-profile-gamepad-mapper.py
```

Il utilise :

```text
D-pad haut/bas : navigation
A : validation
B : annulation
```

Dépendance nécessaire :

```bash
sudo apt install -y xdotool python3-evdev
```

Logs utiles :

```text
/tmp/switch-profile-gamepad.log
/tmp/switch-retropie-profile.log
```

---

## Modifier EmulationStation pour utiliser le launcher Switch

Sauvegarder :

```bash
cp "/home/retropie/.emulationstation/es_systems.cfg" \
   "/home/retropie/.emulationstation/es_systems.cfg.bak-switch-profile-$(date +%Y%m%d-%H%M%S)"
```

Dans le bloc Switch, la commande doit être :

```xml
<command>/home/retropie/RetroPie/roms/emulateurs/custom-launchers/launch-switch-profile.sh %ROM%</command>
```

Attention à ne pas produire un double tag :

```xml
<command><command>...</command></command>
```

Si cela arrive, corriger en :

```xml
<command>/home/retropie/RetroPie/roms/emulateurs/custom-launchers/launch-switch-profile.sh %ROM%</command>
```

---

## PS3 / RPCS3 avec profils joueurs

### Objectif

Ajouter un choix de profil avant le lancement d’un jeu PS3 depuis RetroPie, sur le même modèle que le sélecteur Switch.

Profils utilisés :

```text
Lucas
Nolan
Océane
Oliv
```

Dossiers Linux utilisés :

```text
lucas
nolan
oceane
oliv
```

Le menu de sélection utilise un style sombre inspiré du thème Carbon custom, avec prise en charge de la manette via `xdotool` et `evdev`.

---

### Dossiers RPCS3 utilisés

Sur cette installation, RPCS3 utilise principalement :

```text
/home/retropie/.config/rpcs3
/home/retropie/.cache/rpcs3
```

Le dossier important pour les sauvegardes et données utilisateur est :

```text
/home/retropie/.config/rpcs3/dev_hdd0/home
```

---

### Arborescence des profils PS3

```text
/home/retropie/Documents/save_retropie/ps3_profiles/
├── _common/
│   ├── config/
│   │   ├── dev_flash
│   │   ├── dev_flash2
│   │   ├── dev_flash3
│   │   └── dev_hdd0/
│   │       ├── game
│   │       └── disc
│   └── cache/
│       ├── cache
│       ├── ppu_progs
│       └── spu_progs
├── lucas/
│   ├── config/
│   │   └── dev_hdd0/
│   │       └── home
│   └── cache/
├── nolan/
├── oceane/
└── oliv/
```

Principe :

```text
_common = éléments lourds partagés
chaque profil = saves / trophées / données utilisateur séparées
```

Cela évite de cloner 20 à 30 Go par joueur.

---

### Création des profils PS3

```bash
PROFILES="/home/retropie/Documents/save_retropie/ps3_profiles"

for p in lucas nolan oceane oliv; do
  mkdir -p "$PROFILES/$p/config"
  mkdir -p "$PROFILES/$p/cache"
  mkdir -p "$PROFILES/$p/config/dev_hdd0/home"
done

mkdir -p "$PROFILES/_common/config"
mkdir -p "$PROFILES/_common/cache"
```

---

### Sauvegarde du profil RPCS3 actuel vers Oliv

```bash
PROFILES="/home/retropie/Documents/save_retropie/ps3_profiles"

rsync -avh /home/retropie/.config/rpcs3/ "$PROFILES/oliv/config/"
rsync -avh /home/retropie/.cache/rpcs3/ "$PROFILES/oliv/cache/"
```

---

### Mise en commun des gros dossiers RPCS3

```bash
PROFILES="/home/retropie/Documents/save_retropie/ps3_profiles"

mkdir -p "$PROFILES/_common/config/dev_hdd0"

rsync -avh "$PROFILES/oliv/config/dev_flash/" "$PROFILES/_common/config/dev_flash/"
rsync -avh "$PROFILES/oliv/config/dev_flash2/" "$PROFILES/_common/config/dev_flash2/" 2>/dev/null || true
rsync -avh "$PROFILES/oliv/config/dev_flash3/" "$PROFILES/_common/config/dev_flash3/" 2>/dev/null || true

rsync -avh "$PROFILES/oliv/config/dev_hdd0/game/" "$PROFILES/_common/config/dev_hdd0/game/" 2>/dev/null || true
rsync -avh "$PROFILES/oliv/config/dev_hdd0/disc/" "$PROFILES/_common/config/dev_hdd0/disc/" 2>/dev/null || true

rsync -avh "$PROFILES/oliv/cache/cache/" "$PROFILES/_common/cache/cache/" 2>/dev/null || true
rsync -avh "$PROFILES/oliv/cache/ppu_progs/" "$PROFILES/_common/cache/ppu_progs/" 2>/dev/null || true
rsync -avh "$PROFILES/oliv/cache/spu_progs/" "$PROFILES/_common/cache/spu_progs/" 2>/dev/null || true
```

---

### Reconstruction légère des profils Lucas / Nolan / Océane

Si les dossiers ont été supprimés ou doivent être reconstruits :

```bash
PROFILES="/home/retropie/Documents/save_retropie/ps3_profiles"

for p in lucas nolan oceane; do
  mkdir -p "$PROFILES/$p/config"
  mkdir -p "$PROFILES/$p/cache"
  mkdir -p "$PROFILES/$p/config/dev_hdd0/home"

  rsync -avh \
    --exclude="dev_flash/" \
    --exclude="dev_flash2/" \
    --exclude="dev_flash3/" \
    --exclude="dev_hdd0/game/" \
    --exclude="dev_hdd0/disc/" \
    --exclude="dev_hdd0/home/" \
    "$PROFILES/oliv/config/" \
    "$PROFILES/$p/config/"

  rsync -avh \
    --exclude="cache/" \
    --exclude="ppu_progs/" \
    --exclude="spu_progs/" \
    --exclude="shaderlog/" \
    "$PROFILES/oliv/cache/" \
    "$PROFILES/$p/cache/"
done
```

---

### Liens vers les dossiers communs

```bash
PROFILES="/home/retropie/Documents/save_retropie/ps3_profiles"

for p in lucas nolan oceane oliv; do
  mkdir -p "$PROFILES/$p/config/dev_hdd0"
  mkdir -p "$PROFILES/$p/cache"

  rm -rf "$PROFILES/$p/config/dev_flash"
  ln -s "$PROFILES/_common/config/dev_flash" "$PROFILES/$p/config/dev_flash"

  rm -rf "$PROFILES/$p/config/dev_flash2"
  ln -s "$PROFILES/_common/config/dev_flash2" "$PROFILES/$p/config/dev_flash2"

  rm -rf "$PROFILES/$p/config/dev_flash3"
  ln -s "$PROFILES/_common/config/dev_flash3" "$PROFILES/$p/config/dev_flash3"

  rm -rf "$PROFILES/$p/config/dev_hdd0/game"
  ln -s "$PROFILES/_common/config/dev_hdd0/game" "$PROFILES/$p/config/dev_hdd0/game"

  rm -rf "$PROFILES/$p/config/dev_hdd0/disc"
  ln -s "$PROFILES/_common/config/dev_hdd0/disc" "$PROFILES/$p/config/dev_hdd0/disc"

  rm -rf "$PROFILES/$p/cache/cache"
  ln -s "$PROFILES/_common/cache/cache" "$PROFILES/$p/cache/cache"

  rm -rf "$PROFILES/$p/cache/ppu_progs"
  ln -s "$PROFILES/_common/cache/ppu_progs" "$PROFILES/$p/cache/ppu_progs"

  rm -rf "$PROFILES/$p/cache/spu_progs"
  ln -s "$PROFILES/_common/cache/spu_progs" "$PROFILES/$p/cache/spu_progs"
done
```

Résultat attendu :

```text
dev_hdd0/home = vrai dossier séparé par profil
dev_hdd0/game = lien vers _common
dev_flash     = lien vers _common
cache/cache   = lien vers _common
```

---

### Launcher PS3 avec profil

Le launcher principal est :

```text
/home/retropie/RetroPie/roms/emulateurs/custom-launchers/launch-ps3-profile.sh
```

Il fait :

```text
1. affiche le menu profil PS3 style Carbon ;
2. permet de choisir Lucas, Nolan, Océane ou Oliv ;
3. bascule /home/retropie/.config/rpcs3 vers le profil choisi ;
4. bascule /home/retropie/.cache/rpcs3 vers le profil choisi ;
5. appelle le launcher PS3 d’origine.
```

Le launcher d’origine est conservé comme cœur de lancement :

```text
/home/retropie/RetroPie/roms/emulateurs/custom-launchers/launch-ps3-core.sh
```

Ce point est important, car les fichiers `.PS3` sont des raccourcis personnalisés. Ils ne doivent pas être envoyés directement à RPCS3 sans passer par le launcher existant.

---

### Commande EmulationStation pour PS3

Dans :

```text
/home/retropie/.emulationstation/es_systems.cfg
```

Le bloc PS3 doit contenir :

```xml
<command>/home/retropie/RetroPie/roms/emulateurs/custom-launchers/launch-ps3-profile.sh %ROM%</command>
```

Ancienne commande remplacée :

```xml
<command>/home/retropie/RetroPie/roms/emulateurs/custom-launchers/launch-ps3.sh %ROM%</command>
```

Vérification :

```bash
grep -n -A10 -B4 -i "<name>ps3</name>" /home/retropie/.emulationstation/es_systems.cfg
grep -n "<command><command>" /home/retropie/.emulationstation/es_systems.cfg || echo "Pas de double command"
```

---

### Test direct

```bash
"/home/retropie/RetroPie/roms/emulateurs/custom-launchers/launch-ps3-profile.sh" \
"/home/retropie/RetroPie/roms/PS3/Prince of Persia Trilogy (Europe) (En,Fr,De,Es,It).PS3"
```

Si le test direct fonctionne mais pas RetroPie, vérifier que `es_systems.cfg` pointe bien vers `launch-ps3-profile.sh`.

---

### Logs PS3 utiles

```text
/tmp/ps3-retropie-profile.log
/tmp/switch-profile-gamepad.log
```

Commande :

```bash
tail -n 160 /tmp/ps3-retropie-profile.log
```

---

### Exclusion Git

Les profils PS3 ne doivent pas être versionnés.

Ajouter dans `.gitignore` :

```gitignore
ps3_profiles/
```

# Partie 4 : Xbox 360 / Xenia Canary

## Objectif

Remplacer le lancement via Xenia Manager par un lancement direct :

```text
RetroPie -> fichier .xenia -> launch-xenia-canary.sh -> Xenia Canary
```

Xenia Manager devient optionnel. Il peut rester utile pour configurer ou tester, mais il n’est plus nécessaire pour lancer les jeux depuis RetroPie.

---

## Format des fichiers `.xenia`

Exemple :

```json
{
  "type": "game",
  "title": "SONIC UNLEASHED",
  "game_id": "53450812",
  "game_path": "C:\\Xenia_Canary\\Jeux\\Sonic Unleashed (USA) (En,Ja,Fr,De,Es,It).iso",
  "config_path": "Emulators\\Xenia Canary\\config\\SONIC UNLEASHED.config.toml",
  "xenia_version": "Canary"
}
```

Le launcher lit principalement :

```text
game_path
title
config_path
```

---

## Réglages Xenia utilisés

La configuration testée fonctionne avec :

```toml
hid = "xinput"
gpu = "vulkan"
fullscreen = true
```

Le mode D3D12 avec :

```toml
render_target_path_d3d12 = "rtv"
```

a été testé mais a provoqué un écran noir sur certains jeux. La configuration stable actuelle est donc Vulkan.

---

## Sauvegardes Xenia

Les sauvegardes Xenia sont liées à un profil.

Dossiers observés :

```text
/home/retropie/Games/xenia-emu/drive_c/Xenia_Canary/content
/home/retropie/Games/xenia-emu/drive_c/Xenia_Canary/Emulators/Xenia Canary/content
```

Dans certains cas, les sauvegardes utilisées par Xenia Manager doivent être recopiées vers le dossier Xenia direct.

Exemple de restauration des profils Manager vers Xenia direct :

```bash
ROOT_CONTENT="/home/retropie/Games/xenia-emu/drive_c/Xenia_Canary/content"
MANAGER_CONTENT="/home/retropie/Games/xenia-emu/drive_c/Xenia_Canary/Emulators/Xenia Canary/content"

BAK="/home/retropie/Documents/save_retropie/saves_xenia/backup-profils-xenia-direct-$(date +%Y%m%d-%H%M%S)"

mkdir -p "$BAK"
cp -a "$ROOT_CONTENT" "$BAK/content-direct"

for src in "$MANAGER_CONTENT"/*; do
  [ -d "$src" ] || continue

  profile="$(basename "$src")"
  dst="$ROOT_CONTENT/$profile"

  mkdir -p "$dst"
  rsync -avh --delete "$src"/ "$dst"/
done
```

---

# Partie 5 : nettoyage avant GitHub

## Ranger les backups

```bash
cd /home/retropie/Documents/save_retropie/Manuels

mkdir -p backups/scripts

find scripts -maxdepth 1 -type f \( -name "*.bak*" -o -name "*.OK-*" \) \
  -print -exec mv {} backups/scripts/ \;
```

## Supprimer les caches Python

```bash
find scripts -type d -name "__pycache__" -exec rm -rf {} +
```

## Vérifier ce qui va partir

```bash
cd /home/retropie/Documents/save_retropie

git status --ignored
git status
```

Contrôle anti-boulette :

```bash
git status --short | grep -E 'pdf|backup|bak|__pycache__|\.csv|\.zip|\.iso|\.rvz|\.chd|\.bin|\.keys|switch_profiles' || echo "Rien de sale à envoyer"
```

---

# Partie 6 : GitHub

## Dépôt distant

```bash
git remote set-url origin git@github.com:chabad26/retropie-save-tools.git
```

## Ajouter les fichiers utiles

```bash
git add README.md
git add .gitignore
git add Manuels/scripts/*.py
git add Manuels/scripts/*.sh
```

## Commit

```bash
git commit -m "Update RetroPie tools documentation"
```

## Push

```bash
git branch -M main
git push -u origin main
```

---

# Feuille de route

## Fait

```text
Manuels PDF
Ouverture en jeu avec L3
Message "Aucun manuel disponible"
Switch avec profils Lucas / Oliv / Nolan / Océane
Xenia Canary direct
Sauvegardes Xenia restaurables par profil
```

## À faire

```text
PS3 : stabilisation RPCS3, trop de crashs actuellement
PS3 : étudier la gestion de profils
Xbox 360 : améliorer la gestion de profils Xenia
Xbox 360 : appliquer éventuellement les configs par jeu
Moissonneuse V3 : ajout d’une source alternative à Archive.org
```

---

## État du projet

Projet personnel fonctionnel mais encore adapté à une configuration précise.

Objectif : fournir un kit simple pour aider d’autres utilisateurs RetroPie à sauvegarder, restaurer et enrichir leur installation.

Certains chemins doivent être modifiés selon l’installation de l’utilisateur.

<!-- MANUELS_V3_FR_START -->
# Outils RetroPie Save Tools

Ce dépôt regroupe mes scripts maison pour améliorer mon installation RetroPie / EmulationStation.

Le projet est encore expérimental, mais plusieurs éléments sont déjà fonctionnels sur ma configuration.

## Objectifs

- Ajouter des systèmes non prévus de base dans RetroPie.
- Gérer des profils utilisateurs pour certains émulateurs.
- Rechercher et télécharger des manuels de jeux.
- Relier automatiquement les manuels aux jeux dans les `gamelist.xml`.
- Ouvrir un manuel en jeu avec une combinaison de touches.

## Systèmes ajoutés / améliorés

### Nintendo Switch

Gestion via Eden avec profils séparés :

- Lucas
- Nolan
- Océane
- Oliv

Chaque profil possède ses propres dossiers de configuration et de sauvegarde, avec certains éléments communs comme les clés.

### PlayStation 3

Gestion via RPCS3 avec profils séparés.

Les dossiers lourds sont partagés quand c’est possible, tandis que les sauvegardes restent propres à chaque profil.

### Xbox 360

Gestion via Xenia Canary avec sélection de profil au lancement.

Chaque profil possède son propre dossier `content`, ce qui permet de séparer les sauvegardes.

## Manuels de jeux

Les scripts du dossier `Manuels/scripts` permettent de rechercher, télécharger et associer des manuels PDF aux jeux RetroPie.

### Sources utilisées

La moissonneuse V3 utilise plusieurs sources :

1. `localcsv`  
   Liens validés manuellement dans un CSV local.

2. `notipix`  
   Source française pour les notices rétro.  
   Le site renvoie souvent vers des fichiers hébergés sur Google Drive.

3. `archive`  
   Recherche de secours via Archive.org.

4. `replacementdocs`  
   Conservé en expérimental, mais actuellement peu fiable.

### Scripts principaux

```text
Manuels/scripts/scan-gamelists-manuels.py
Manuels/scripts/prepare-recherche-manuels.py
Manuels/scripts/moissonner-manuels-v3.py
Manuels/scripts/moissonner-manuels-v3-cute.py
Manuels/scripts/update-gamelists-manuals-from-pdfs.py
Manuels/scripts/open-current-manual.sh
Manuels/scripts/set-current-manual.py
Manuels/scripts/manual-hotkey-watcher.py
Manuels/scripts/show-current-manual-status.sh
Moissonneuse V3

Utilisation simple :

cd /home/retropie/Documents/save_retropie/Manuels
scripts/moissonner-manuels-v3.py nes --limit 20 --debug

Téléchargement prudent :

scripts/moissonner-manuels-v3.py nes --download --sleep 8

Sources par défaut :

localcsv,notipix,archive
Moissonneuse V3 Cute

La version cute est un lanceur plus confortable autour de la V3.

Elle ajoute :

choix de console ;
traitement de toutes les consoles ;
reprise après interruption ;
mode dry-run ou téléchargement ;
pause entre les requêtes.

Exemples :

scripts/moissonner-manuels-v3-cute.py --choose --limit 20 --debug
scripts/moissonner-manuels-v3-cute.py --choose --download --sleep 4
scripts/moissonner-manuels-v3-cute.py --all --download --sleep 6
scripts/moissonner-manuels-v3-cute.py --resume
Ouverture des manuels en jeu

Au lancement d’un jeu, le système vérifie si un manuel est disponible.

Si un manuel existe, une notification s’affiche avec la combinaison :

L3 + R3

Pendant le jeu, appuyer sur L3 + R3 ouvre le manuel associé.

Le watcher utilisé est :

Manuels/scripts/manual-hotkey-watcher.py

Le script d’affichage au lancement est :

Manuels/scripts/show-current-manual-status.sh
Organisation des dossiers
/home/retropie/Documents/save_retropie/
├── Manuels/
│   ├── pdf/
│   ├── rapports/
│   └── scripts/
├── ps3_profiles/
├── switch_profiles/
└── xbox360_profiles/

Les dossiers de profils et les PDF téléchargés ne sont pas destinés à être poussés sur GitHub.

État actuel

Fonctionnel sur ma configuration :

profils Switch ;
profils PS3 ;
profils Xbox 360 ;
recherche de manuels avec Archive.org ;
recherche de manuels français avec Notipix ;
téléchargement depuis Google Drive quand le lien est public ;
association des manuels dans les gamelist.xml ;
notification au lancement du jeu ;
ouverture en jeu avec L3 + R3.

Le projet reste expérimental et pensé pour mon installation RetroPie.
Certains chemins peuvent nécessiter une adaptation sur une autre machine.

<!-- MANUELS_V3_FR_END -->

## Fonctionnalités principales

### Gestion des profils joueurs

Les émulateurs suivants peuvent utiliser plusieurs profils indépendants :

- Nintendo Switch (Eden)
- Sony PlayStation 3 (RPCS3)
- Microsoft Xbox 360 (Xenia Canary)

Chaque joueur possède son propre environnement :

- sauvegardes
- paramètres
- cache
- shaders
- données utilisateur

Profils actuellement utilisés :

- Lucas
- Nolan
- Océane
- Oliv

Le choix du profil est proposé au lancement du jeu via une interface inspirée du thème Carbon de RetroPie, entièrement pilotable à la manette.

## Gestion des manuels

Le projet permet désormais de :

- rechercher automatiquement les manuels
- télécharger les PDF
- associer automatiquement les manuels aux `gamelist.xml`
- contrôler la qualité des PDF
- optimiser automatiquement les PDF trop volumineux
- détecter les liens cassés
- vérifier les PDF chiffrés
- détecter les fichiers anormalement petits ou volumineux

## Sources utilisées

La recherche de manuels utilise actuellement :

- Archive.org
- Notipix

Les téléchargements sont réalisés uniquement lorsque le manuel est disponible publiquement.

## Consultation des manuels pendant le jeu

Lorsqu'un manuel est associé au jeu :

- une notification indique qu'un manuel est disponible au lancement ;
- la combinaison **L3 + R3** ouvre le manuel sans quitter le jeu ;
- le jeu continue de tourner en arrière-plan ;
- le lecteur PDF est entièrement contrôlable à la manette.

Contrôles :

| Action | Manette |
|---------|----------|
| Ouvrir le manuel | L3 + R3 |
| Défiler | Croix directionnelle ou Stick |
| Page suivante | Droite |
| Page précédente | Gauche |
| Zoom + | R1 |
| Zoom - | L1 |
| Ajuster la largeur | Start |
| Fermer le manuel | A ou B |

## Contrôle qualité des manuels

Un outil dédié permet de vérifier automatiquement :

- nombre de pages
- poids du PDF
- poids moyen par page
- PDF chiffrés
- liens cassés dans les gamelists
- manuels présents mais non associés
- fichiers suspects

Un rapport CSV est généré automatiquement.

## Optimisation automatique

Les PDF volumineux peuvent être optimisés grâce à Ghostscript.

Fonctionnalités :

- sauvegarde automatique de l'original
- plusieurs niveaux de qualité
- mode Dry-Run
- optimisation par dossier ou par fichier
- rapport détaillé des gains obtenus

## Diagnostic RetroPie

Le script `check-retropie.py` permet de contrôler rapidement l'installation.

Il vérifie notamment :

- dépendances Python
- présence des émulateurs
- scripts de lancement
- profils utilisateurs
- manuels
- gamelists
- liens symboliques
- qualité des PDF

Il peut également effectuer certaines réparations automatiquement.

## Menu RetroPie Tools

Un menu unique permet désormais d'accéder aux principales fonctionnalités :

- téléchargement des manuels
- contrôle qualité
- optimisation des PDF
- diagnostic
- réparation
- résumé des statistiques
- informations sur les profils

Objectif : rendre l'ensemble du projet accessible sans avoir à lancer chaque script manuellement.

## Roadmap

### ✔ Terminé

- Gestion des profils Switch
- Gestion des profils PS3
- Gestion des profils Xbox 360
- Téléchargement automatique des manuels
- Association automatique aux gamelists
- Consultation des manuels pendant le jeu
- Contrôle qualité des PDF
- Optimisation automatique des PDF
- Diagnostic de l'installation
- Interface utilisateur unifiée (`retropie-tools`)
- Amélioration de l'interface Carbon
- Compatibilité avec davantage de manettes
- Scraper des médias

### 💡 Prévu

- Mise à jour automatique des manuels
- Traductions (README anglais)
- Création d'un installeur "one-click"

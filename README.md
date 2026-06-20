# RetroPie Save Tools

Scripts personnels pour sauvegarder, réinstaller et enrichir une installation RetroPie / EmulationStation.

Ce dépôt contient principalement :

* des scripts de déploiement pour consoles personnalisées dans RetroPie ;
* des scripts de génération de raccourcis et de marquees ;
* une moissonneuse de manuels PDF pour associer automatiquement des notices aux jeux ;
* une organisation pensée pour survivre à une réinstallation propre.

> Ce dépôt ne contient pas de ROMs, BIOS, jeux, manuels PDF téléchargés, ni fichiers protégés.
> Il fournit uniquement des scripts et de la documentation.

---

## Objectif du projet

Le but est de centraliser les scripts utiles à une configuration RetroPie personnalisée :

1. intégrer des consoles supplémentaires dans EmulationStation ;
2. générer des raccourcis pour certains émulateurs ;
3. générer des éléments visuels comme les marquees ;
4. rechercher des manuels PDF de jeux ;
5. mettre à jour les `gamelist.xml` pour associer les manuels aux jeux ;
6. faciliter la restauration après formatage ou changement de machine.

---

## Arborescence recommandée

L’arborescence locale utilisée pendant le développement est :

```text
/home/retropie/Documents/save_retropie/
├── Manuels/
│   └── scripts/
│       ├── scan-gamelists-manuels.py
│       ├── prepare-recherche-manuels.py
│       ├── moissonner-manuels-archive-v2-cute.py
│       └── download-manuels-valides.py
│
└── script déployement PS3, xbox, xbox360 SWITCH/
    ├── integrer-consoles-retropie.sh
    ├── integrer_xenia_retropie.sh
    ├── generer-raccourcis-ps3.sh
    ├── generer-marquees-autre.py
    ├── generer-marquees-xbox360-png.py
    └── generer-marquees-xbox360.py
```

Les manuels PDF, rapports CSV, backups et caches ne sont pas versionnés.

---

## Prérequis

Système testé :

* Ubuntu avec RetroPie installé ;
* EmulationStation ;
* Python 3 ;
* accès Internet pour la recherche de manuels ;
* Git si l’on souhaite cloner ou versionner le projet.

Installer les dépendances minimales :

```bash
sudo apt update
sudo apt install -y python3 git rsync
```

---

## Organisation des manuels

Le dossier réel des manuels peut être placé dans :

```text
/home/retropie/Documents/save_retropie/Manuels/pdf
```

Puis exposé à RetroPie via un lien symbolique :

```bash
ln -s /home/retropie/Documents/save_retropie/Manuels/pdf \
      /home/retropie/RetroPie/manuals
```

Ainsi, EmulationStation continue de lire :

```text
/home/retropie/RetroPie/manuals
```

mais les fichiers sont réellement stockés dans le dossier de sauvegarde.

---

## Ordre d’exécution recommandé pour les manuels

### 1. Scanner les gamelists

Ce script lit les `gamelist.xml` existants et génère une liste brute des jeux.

```bash
cd /home/retropie/Documents/save_retropie/Manuels

scripts/scan-gamelists-manuels.py
```

Résultat attendu :

```text
liste-jeux-pour-manuels.csv
```

### 2. Nettoyer les noms de jeux

Ce script nettoie les noms issus des ROMs ou des gamelists :

* suppression des régions ;
* suppression des tags `[!]`, `[f1]`, etc. ;
* suppression des versions inutiles ;
* génération d’un nom de recherche propre.

```bash
scripts/prepare-recherche-manuels.py
```

Résultat attendu :

```text
liste-jeux-pour-manuels-clean.csv
```

Les CSV peuvent être rangés dans :

```text
/home/retropie/Documents/save_retropie/Manuels/rapports
```

### 3. Tester la recherche de manuels

La moissonneuse cherche des manuels sur Archive.org sans télécharger en mode dry-run.

```bash
scripts/moissonner-manuels-archive-v2-cute.py snes --limit 20 --debug
```

Options utiles :

```bash
--limit 20       limite le nombre de jeux testés
--debug          affiche les candidats trouvés
--language fr    cherche en priorité en français
--download       télécharge réellement les PDF
--choose         propose une console au démarrage
--all            traite toutes les consoles
--resume         reprend une session interrompue
--restart        ignore la session précédente
```

### 4. Télécharger pour une console

Une fois le test validé :

```bash
scripts/moissonner-manuels-archive-v2-cute.py snes --download
```

### 5. Télécharger avec choix interactif

```bash
scripts/moissonner-manuels-archive-v2-cute.py --choose --download
```

### 6. Traiter toutes les consoles

À utiliser avec prudence :

```bash
scripts/moissonner-manuels-archive-v2-cute.py --all --download
```

---

## Reprise et arrêt propre

La version `cute` peut sauvegarder sa progression.

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
scripts/moissonner-manuels-archive-v2-cute.py snes --resume --download
```

Ou simplement relancer le script : il proposera de reprendre ou de recommencer.

---

## Mise à jour des gamelists

Quand un manuel est téléchargé, le script peut ajouter une balise :

```xml
<manual>/home/retropie/RetroPie/manuals/snes/Nom du jeu.pdf</manual>
```

dans le fichier :

```text
/home/retropie/.emulationstation/gamelists/<system>/gamelist.xml
```

Une sauvegarde du fichier `gamelist.xml` est créée avant modification.

---

## Scripts consoles personnalisées

Les scripts de déploiement consoles servent à intégrer des systèmes personnalisés dans EmulationStation.

Exemples :

```text
PS3
Xbox
Xbox 360
Switch
```

Scripts principaux :

```text
integrer-consoles-retropie.sh
integrer_xenia_retropie.sh
generer-raccourcis-ps3.sh
generer-marquees-autre.py
generer-marquees-xbox360-png.py
```

Ces scripts doivent être adaptés selon les chemins locaux des émulateurs.

---

## Exemple de flux complet

```bash
cd /home/retropie/Documents/save_retropie/Manuels

scripts/scan-gamelists-manuels.py
scripts/prepare-recherche-manuels.py

scripts/moissonner-manuels-archive-v2-cute.py snes --limit 20 --debug

scripts/moissonner-manuels-archive-v2-cute.py snes --download
```

---

## Ce qui n’est pas inclus

Ce dépôt ne doit pas contenir :

* ROMs ;
* BIOS ;
* ISOs ;
* fichiers CHD ;
* manuels PDF téléchargés ;
* caches ;
* backups locaux volumineux ;
* fichiers personnels.

Ces fichiers doivent rester locaux.

---

## Notes légales

Les scripts peuvent aider à rechercher des manuels disponibles publiquement sur Internet.

Chaque utilisateur est responsable :

* de respecter les droits d’auteur ;
* de ne pas redistribuer de fichiers protégés ;
* de vérifier les conditions d’utilisation des sources consultées ;
* de ne publier que du code et de la documentation.

---

## Licence

À définir.

Suggestions :

* MIT pour un partage libre et simple ;
* GPLv3 si vous souhaitez que les versions modifiées restent libres.

---

## État du projet

Projet personnel en cours de nettoyage avant publication publique.

Objectif : fournir un kit simple pour aider d’autres utilisateurs RetroPie à sauvegarder, restaurer et enrichir leur installation.

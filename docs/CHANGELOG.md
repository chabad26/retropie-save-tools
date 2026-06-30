# Changelog

## 0.6.0-dev

### Ajouté

- Architecture modulaire avec dossier `plugins/`.
- Chargement automatique des plugins.
- Menu Plugins dynamique.
- Fiche détail plugin :
  - lancer
  - à propos
  - dépendances
- Dashboard dynamique alimenté par les statuts des plugins.
- Plugin Manuels.
- Plugin Profils joueurs.
- Plugin Manettes.
- Plugin Diagnostic.
- Plugin Rapports / logs.
- Plugin Paramètres.
- Plugin Git / Maintenance.
- Configuration centrale `config/settings.yml`.

### Modifié

- `retropie-tools` devient le cœur de l’application.
- Les fonctionnalités principales migrent progressivement vers des plugins.
- Le menu principal est simplifié :
  - Tableau de bord
  - Plugins
  - Quitter

### Notes

- Steam et Wii U ne sont pas ciblés sur cette machine.
- La cible actuelle est RetroPie avec les consoles ajoutées à EmulationStation.
MD

cat > docs/architecture.md <<'MD'
# Architecture RetroPie Toolbox

RetroPie Toolbox est organisé autour d’un cœur minimal et de plugins.

## Cœur

Le fichier principal est :

```text
retropie-tools

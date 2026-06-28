# API des plugins

Un plugin est un dossier placé dans :

plugins/<nom>/

Il contient au minimum :

plugin.py

Le plugin expose :

- PLUGIN
- run(app)
- status()

PLUGIN doit contenir :

- id
- name
- description
- version
- author
- order
- requires

status() retourne :

{
    "state":"ok",
    "title":"...",
    "message":"..."
}

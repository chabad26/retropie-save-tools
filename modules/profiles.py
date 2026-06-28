from pathlib import Path
import shutil
from .core import load_settings, CONFIG
import yaml


PROFILE_DIRS = {
    "switch": ["cache", "config", "share"],
    "ps3": ["cache", "config", "config/dev_hdd0/home"],
    "xbox360": ["content"],
}


def save_settings(data):
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def player_key(name):
    return name.strip().lower().replace("é", "e").replace("è", "e").replace("ê", "e").replace(" ", "_")


def base_paths():
    root = Path(load_settings()["paths"]["root"])
    return {
        "switch": root / "switch_profiles",
        "ps3": root / "ps3_profiles",
        "xbox360": root / "xbox360_profiles",
    }


def list_players():
    settings = load_settings()
    return settings.get("players", [])


def create_player(name):
    key = player_key(name)
    if not key:
        return False, "Nom vide."

    settings = load_settings()
    players = settings.setdefault("players", [])

    if key not in players:
        players.append(key)
        save_settings(settings)

    paths = base_paths()

    for system, base in paths.items():
        for sub in PROFILE_DIRS[system]:
            (base / key / sub).mkdir(parents=True, exist_ok=True)

    return True, f"Profil créé : {key}"


def delete_player(name):
    key = player_key(name)
    if not key:
        return False, "Nom vide."

    settings = load_settings()
    players = settings.setdefault("players", [])

    if key in players:
        settings["players"] = [p for p in players if p != key]
        save_settings(settings)

    paths = base_paths()

    for base in paths.values():
        target = base / key
        if target.exists():
            backup = base / f"{key}.deleted"
            if backup.exists():
                shutil.rmtree(backup)
            target.rename(backup)

    return True, f"Profil supprimé de la config et renommé en .deleted : {key}"


def rename_player(old_name, new_name):
    old = player_key(old_name)
    new = player_key(new_name)

    if not old or not new:
        return False, "Nom invalide."

    settings = load_settings()
    players = settings.setdefault("players", [])

    settings["players"] = [new if p == old else p for p in players]

    if new not in settings["players"]:
        settings["players"].append(new)

    save_settings(settings)

    paths = base_paths()

    for base in paths.values():
        src = base / old
        dst = base / new

        if src.exists() and not dst.exists():
            src.rename(dst)

    return True, f"Profil renommé : {old} -> {new}"


def info_text():
    settings = load_settings()
    root = Path(settings["paths"]["root"])
    players = ", ".join(settings.get("players", []))

    return (
        f"Profils gérés : {players}\n\n"
        f"Switch / Eden :\n{root / 'switch_profiles'}\n\n"
        f"PS3 / RPCS3 :\n{root / 'ps3_profiles'}\n\n"
        f"Xbox 360 / Xenia :\n{root / 'xbox360_profiles'}\n\n"
        "Le choix du profil se fait au lancement du jeu."
    )

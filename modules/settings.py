from pathlib import Path
import yaml
from .core import CONFIG, load_settings

def save_settings(data):
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)

def get_text():
    return CONFIG.read_text(encoding="utf-8") if CONFIG.is_file() else "Aucune configuration."

def set_manual_sleep(value):
    data = load_settings()
    data.setdefault("manuals", {})["sleep"] = int(value)
    save_settings(data)

def set_manual_sources(value):
    data = load_settings()
    data.setdefault("manuals", {})["sources"] = value
    save_settings(data)

def set_quality_min_size(value):
    data = load_settings()
    data.setdefault("manuals", {})["quality_min_size"] = value
    save_settings(data)

def add_player(name):
    data = load_settings()
    players = data.setdefault("players", [])
    key = name.strip().lower()
    if key and key not in players:
        players.append(key)
    save_settings(data)

def remove_player(name):
    data = load_settings()
    players = data.setdefault("players", [])
    key = name.strip().lower()
    data["players"] = [p for p in players if p != key]
    save_settings(data)

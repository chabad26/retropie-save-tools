from pathlib import Path
import subprocess
import yaml

ROOT = Path.home() / "Documents/save_retropie"
CONFIG = ROOT / "config/settings.yml"

def load_settings():
    if not CONFIG.is_file():
        return {}
    with CONFIG.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def run(command):
    return subprocess.call([str(x) for x in command])

def path_from_config(*keys, default=None):
    data = load_settings()
    cur = data
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return Path(default) if default else None
        cur = cur[key]
    return Path(cur)

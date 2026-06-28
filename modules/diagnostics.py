from pathlib import Path
from .core import load_settings, run


def root():
    return Path(load_settings()["paths"]["root"])


def quick():
    return run([root() / "scripts/check-retropie.py", "--no-quality"])


def full():
    return run([root() / "scripts/check-retropie.py", "--doctor", "--stats"])


def fix():
    return run([root() / "scripts/check-retropie.py", "--fix", "--doctor", "--stats"])

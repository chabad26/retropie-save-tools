from pathlib import Path
from .core import load_settings, run

def manuals_root():
    return Path(load_settings()["paths"]["manuals"])

def detect():
    return run([manuals_root() / "scripts/controller-detect.py"])

def test():
    return run([manuals_root() / "scripts/controller-test.py"])

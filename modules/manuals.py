from pathlib import Path
from .core import load_settings, run

def root():
    settings = load_settings()
    return Path(settings["paths"]["manuals"])

def harvest(system=None, all_systems=False, download=False, debug=True, sleep=None):
    settings = load_settings()
    manuals = root()
    cmd = [manuals / "scripts/moissonner-manuels-v3-cute.py"]

    if all_systems:
        cmd.append("--all")
    elif system:
        cmd.append(system)
    else:
        cmd.append("--choose")

    if download:
        cmd.append("--download")
    elif debug:
        cmd.append("--debug")

    cmd += ["--sleep", str(sleep or settings.get("manuals", {}).get("sleep", 4))]
    return run(cmd)

def check(with_gamelists=False):
    cmd = [root() / "scripts/check-manuels.py", "--only-problems"]
    if with_gamelists:
        cmd.append("--check-gamelists")
    return run(cmd)

def summary():
    return run([root() / "scripts/resume-qualite-manuels.py", "--limit", "40"])

def optimize(dry_run=True):
    cmd = [root() / "scripts/optimize-manuels.py", "--only-problems", "--min-size", "50M"]
    if dry_run:
        cmd.append("--dry-run")
    return run(cmd)

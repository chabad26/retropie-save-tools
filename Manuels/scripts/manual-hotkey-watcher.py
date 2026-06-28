#!/usr/bin/env python3

from evdev import InputDevice, ecodes
from pathlib import Path
import json, os, subprocess, time, select, sys

DETECT = "/home/retropie/Documents/save_retropie/Manuels/scripts/controller-detect.py"
MAP_FILE = Path("/home/retropie/Documents/save_retropie/Manuels/config/controller-map.json")
OPEN_SCRIPT = "/home/retropie/Documents/save_retropie/Manuels/scripts/open-current-manual.sh"
LOG = Path("/tmp/retropie-manual-hotkey.log")
COOLDOWN_SECONDS = 2.5

def log(msg):
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{time.ctime()} | {msg}\n")

def code_from_name(name):
    v = getattr(ecodes, name, None)
    return v if isinstance(v, int) else None

def load_combos():
    combos = [
        ["BTN_THUMBL", "BTN_THUMBR"],
        ["BTN_SELECT", "BTN_START"],
    ]

    try:
        if MAP_FILE.is_file():
            data = json.loads(MAP_FILE.read_text(encoding="utf-8"))
            hotkeys = data.get("hotkeys", {})

            if "open_manual_combos" in hotkeys:
                combos = hotkeys["open_manual_combos"]
            elif "open_manual_combo" in hotkeys:
                combos = [hotkeys["open_manual_combo"]]

    except Exception as e:
        log(f"Mapping illisible, fallback : {e}")

    resolved = []

    for combo in combos:
        codes = {code_from_name(name) for name in combo}
        codes = {code for code in codes if code is not None}

        if codes:
            resolved.append(codes)

    return resolved or [{ecodes.BTN_THUMBL, ecodes.BTN_THUMBR}]

def detect_all():
    try:
        out = subprocess.check_output([DETECT, "--json"], text=True, stderr=subprocess.DEVNULL)
        data = json.loads(out)
        return [d["path"] for d in data if d.get("path")]
    except Exception as e:
        log(f"Auto-détection impossible : {e}")
        return []

def open_manual():
    log("Ouverture manuel demandée")
    env = os.environ.copy()
    env["DISPLAY"] = ":1"
    env["XAUTHORITY"] = "/home/retropie/.Xauthority"
    subprocess.Popen([OPEN_SCRIPT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)

paths = sys.argv[1:] if len(sys.argv) > 1 else detect_all()

if not paths:
    paths = ["/dev/input/by-id/usb-PowerA_NSW_wired_controller-event-joystick"]

devices = []
for path in paths:
    try:
        dev = InputDevice(path)
        devices.append(dev)
        log(f"Watcher écoute : {path} | name={dev.name} | fd={dev.fd}")
    except Exception as e:
        log(f"Impossible d'ouvrir {path}: {e}")

if not devices:
    log("Aucun device ouvert, arrêt")
    sys.exit(1)

combo_sets = load_combos()
log(f"Combos actifs codes : {[sorted(c) for c in combo_sets]}")

pressed_by_fd = {dev.fd: set() for dev in devices}
last_trigger = 0.0
armed_by_fd = {dev.fd: True for dev in devices}

while True:
    readable, _, _ = select.select(devices, [], [])

    for dev in readable:
        for event in dev.read():
            if event.type != ecodes.EV_KEY:
                continue

            if not any(event.code in combo for combo in combo_sets):
                continue

            pressed = pressed_by_fd[dev.fd]

            if event.value != 0:
                pressed.add(event.code)
            else:
                pressed.discard(event.code)

            log(f"{dev.name} fd={dev.fd} pressed={sorted(pressed)}")

            now = time.time()

            active_combo = next((combo for combo in combo_sets if combo.issubset(pressed)), None)

            if active_combo and now - last_trigger >= COOLDOWN_SECONDS:
                log(f"Combo détecté sur {dev.name} codes={sorted(active_combo)}")
                open_manual()
                last_trigger = now

            if not active_combo:
                armed_by_fd[dev.fd] = True

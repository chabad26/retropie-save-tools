#!/usr/bin/env python3

from evdev import InputDevice, ecodes
from pathlib import Path
import json
import os
import subprocess
import sys
import time

DETECT = "/home/retropie/Documents/save_retropie/Manuels/scripts/controller-detect.py"
MAP_FILE = Path("/home/retropie/Documents/save_retropie/Manuels/config/controller-map.json")
HELP_SCRIPT = "/home/retropie/Documents/save_retropie/Manuels/scripts/show-manual-controls.sh"

LOG = Path("/tmp/retropie-manual-pdf-gamepad.log")

COOLDOWN = 0.18
last_action = 0.0


DEFAULT_MAP = {
    "quit": ["BTN_A", "BTN_B"],
    "help": ["BTN_X", "BTN_Y"],
    "zoom_out": ["BTN_TL"],
    "zoom_in": ["BTN_TR"],
    "fit": ["BTN_SELECT", "BTN_START"],
    "dpad": {
        "up": ["ABS_HAT0Y", -1],
        "down": ["ABS_HAT0Y", 1],
        "left": ["ABS_HAT0X", -1],
        "right": ["ABS_HAT0X", 1]
    }
}


def log(msg):
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{time.ctime()} | {msg}\n")


def autodetect_controller() -> str:
    try:
        out = subprocess.check_output(
            [DETECT, "--first"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if out:
            return out
    except Exception:
        pass

    return "/dev/input/by-id/usb-PowerA_NSW_wired_controller-event-joystick"


def code_from_name(name: str) -> int | None:
    value = getattr(ecodes, name, None)

    if isinstance(value, int):
        return value

    return None


def load_map():
    data = DEFAULT_MAP.copy()

    if MAP_FILE.is_file():
        try:
            raw = json.loads(MAP_FILE.read_text(encoding="utf-8"))
            controls = raw.get("pdf_controls", {})
            data.update(controls)
        except Exception as exc:
            log(f"Mapping illisible, fallback : {exc}")

    key_map = {}

    for action in ["quit", "help", "zoom_out", "zoom_in", "fit"]:
        for name in data.get(action, []):
            code = code_from_name(name)
            if code is not None:
                key_map[code] = action
            else:
                log(f"Code inconnu : {name}")

    dpad_map = {}

    for action, pair in data.get("dpad", {}).items():
        if not isinstance(pair, list) or len(pair) != 2:
            continue

        name, expected = pair
        code = code_from_name(name)

        if code is not None:
            dpad_map[(code, expected)] = action
        else:
            log(f"Code ABS inconnu : {name}")

    return key_map, dpad_map


def xkey(key):
    env = os.environ.copy()
    env["DISPLAY"] = ":1"
    env["XAUTHORITY"] = "/home/retropie/.Xauthority"

    subprocess.Popen(
        ["xdotool", "key", key],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )


def show_help():
    env = os.environ.copy()
    env["DISPLAY"] = ":1"
    env["XAUTHORITY"] = "/home/retropie/.Xauthority"
    env["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path=/run/user/{os.getuid()}/bus"

    subprocess.Popen(
        [HELP_SCRIPT],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )


def do_action(action):
    global last_action

    now = time.time()
    if now - last_action < COOLDOWN:
        return

    last_action = now
    log(action)

    if action == "down":
        xkey("Down")
    elif action == "up":
        xkey("Up")
    elif action == "right":
        xkey("Next")
    elif action == "left":
        xkey("Prior")
    elif action == "zoom_in":
        xkey("plus")
    elif action == "zoom_out":
        xkey("minus")
    elif action == "fit":
        xkey("w")
    elif action == "quit":
        xkey("q")
    elif action == "help":
        show_help()


DEVICE_PATH = sys.argv[1] if len(sys.argv) > 1 else autodetect_controller()

try:
    dev = InputDevice(DEVICE_PATH)
except Exception as exc:
    log(f"Impossible d'ouvrir {DEVICE_PATH}: {exc}")
    sys.exit(1)

key_map, dpad_map = load_map()

log(f"Contrôleur PDF démarré sur {DEVICE_PATH}")
log(f"KEY map : {key_map}")
log(f"DPAD map : {dpad_map}")

for event in dev.read_loop():
    if event.type == ecodes.EV_KEY:
        if event.value != 1:
            continue

        action = key_map.get(event.code)

        if action:
            do_action(action)

    elif event.type == ecodes.EV_ABS:
        action = dpad_map.get((event.code, event.value))

        if action:
            do_action(action)

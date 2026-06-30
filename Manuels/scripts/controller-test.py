#!/usr/bin/env python3

from evdev import InputDevice, ecodes, categorize
from pathlib import Path
import subprocess
import sys

DETECT = "/home/retropie/Documents/save_retropie/Manuels/scripts/controller-detect.py"


def autodetect():
    try:
        out = subprocess.check_output([DETECT, "--first"], text=True).strip()
        if out:
            return out
    except Exception:
        pass
    return ""


device_path = sys.argv[1] if len(sys.argv) > 1 else autodetect()

if not device_path:
    print("❌ Aucune manette détectée")
    sys.exit(1)

dev = InputDevice(device_path)

print(f"🎮 Manette : {dev.name}")
print(f"📍 Device  : {device_path}")
print()
print("Appuie sur les touches à mapper.")
print("Ctrl+C pour quitter.")
print()

try:
    for event in dev.read_loop():
        if event.type == ecodes.EV_KEY:
            key = categorize(event)
            state = {
                0: "UP",
                1: "DOWN",
                2: "HOLD",
            }.get(event.value, str(event.value))

            print(f"KEY  code={event.code:<4} name={key.keycode} state={state}")

        elif event.type == ecodes.EV_ABS:
            name = ecodes.ABS.get(event.code, f"ABS_{event.code}")
            print(f"ABS  code={event.code:<4} name={name} value={event.value}")

except KeyboardInterrupt:
    print("\nFin du test.")

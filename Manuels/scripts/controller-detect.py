#!/usr/bin/env python3

from pathlib import Path
import argparse
import json
import subprocess

BY_ID = Path("/dev/input/by-id")
BY_PATH = Path("/dev/input/by-path")


def device_name(path: Path) -> str:
    try:
        out = subprocess.check_output(
            ["udevadm", "info", "--query=property", "--name", str(path)],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return path.name

    props = {}
    for line in out.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            props[k] = v

    return (
        props.get("ID_MODEL_FROM_DATABASE")
        or props.get("ID_MODEL")
        or props.get("NAME")
        or path.name
    )


def find_devices():
    devices = []

    for root in [BY_ID, BY_PATH]:
        if not root.is_dir():
            continue

        for p in sorted(root.iterdir()):
            name = p.name.lower()

            if "event" not in name:
                continue

            if not any(token in name for token in ["joystick", "gamepad", "controller", "xbox", "nintendo", "playstation", "dualshock", "dualsense", "8bitdo", "powera"]):
                continue

            real = p.resolve()

            devices.append({
                "path": str(p),
                "real": str(real),
                "name": device_name(p),
            })

    # dédup par real path
    unique = {}
    for d in devices:
        unique[d["real"]] = d

    return list(unique.values())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--first", action="store_true")
    args = parser.parse_args()

    devices = find_devices()

    if args.json:
        print(json.dumps(devices, indent=2, ensure_ascii=False))
        return

    if args.first:
        if devices:
            print(devices[0]["path"])
        return

    if not devices:
        print("Aucune manette détectée")
        return

    for i, d in enumerate(devices, start=1):
        print(f"[{i}] {d['name']}")
        print(f"    {d['path']}")
        print(f"    -> {d['real']}")


if __name__ == "__main__":
    main()

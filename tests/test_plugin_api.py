#!/usr/bin/env python3

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modules.plugin import discover_plugins

plugins = discover_plugins()

assert plugins, "Aucun plugin détecté"

errors = []

for plugin in plugins:
    pid = plugin.get("id", "unknown")

    if not plugin.get("valid", True):
        errors.append(f"{pid}: plugin invalide")

    if not callable(plugin.get("commands")):
        errors.append(f"{pid}: commands() absent")

    if not callable(plugin.get("execute")):
        errors.append(f"{pid}: execute(app, command_id) absent")

    if not callable(plugin.get("status")):
        errors.append(f"{pid}: status() absent")

    if not callable(plugin.get("about")):
        errors.append(f"{pid}: about() absent")

    if callable(plugin.get("commands")):
        try:
            commands = plugin["commands"]()
            assert isinstance(commands, list)
            for cmd in commands:
                assert "id" in cmd
                assert "label" in cmd
        except Exception as exc:
            errors.append(f"{pid}: commands() erreur: {exc}")

if errors:
    print("❌ Erreurs Plugin API")
    for err in errors:
        print(" -", err)
    raise SystemExit(1)

print(f"✅ Plugin API OK : {len(plugins)} plugin(s)")
for plugin in plugins:
    print(f" - {plugin['id']} : {plugin['name']}")

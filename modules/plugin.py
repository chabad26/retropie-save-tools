from pathlib import Path
import importlib.util
import sys

PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugins"

REQUIRED_FIELDS = ["id", "name", "description"]


def invalid_plugin(plugin_dir, message):
    return {
        "id": plugin_dir.name,
        "name": f"❌ {plugin_dir.name}",
        "description": message,
        "version": "",
        "author": "",
        "order": 999,
        "requires": [],
        "run": None,
        "status": None,
        "commands": None,
        "execute": None,
        "about": None,
        "path": str(plugin_dir),
        "valid": False,
    }


def validate_plugin(plugin):
    missing = [field for field in REQUIRED_FIELDS if not plugin.get(field)]
    if missing:
        return False, f"Champs manquants : {', '.join(missing)}"
    return True, "OK"


def discover_plugins():
    plugins = []

    if not PLUGIN_DIR.exists():
        return plugins

    for plugin_dir in sorted(PLUGIN_DIR.iterdir()):
        if not plugin_dir.is_dir():
            continue

        plugin_file = plugin_dir / "plugin.py"
        init_file = plugin_dir / "__init__.py"

        if not plugin_file.exists():
            continue

        if not init_file.exists():
            init_file.write_text("", encoding="utf-8")

        package_name = f"retropie_plugin_{plugin_dir.name}"

        spec = importlib.util.spec_from_file_location(
            f"{package_name}.plugin",
            plugin_file,
            submodule_search_locations=[str(plugin_dir)],
        )

        module = importlib.util.module_from_spec(spec)
        sys.modules[package_name] = module
        sys.modules[f"{package_name}.plugin"] = module

        try:
            spec.loader.exec_module(module)
        except Exception as exc:
            plugins.append(invalid_plugin(plugin_dir, f"Erreur de chargement : {exc}"))
            continue

        if not hasattr(module, "PLUGIN"):
            plugins.append(invalid_plugin(plugin_dir, "Variable PLUGIN absente"))
            continue

        plugin = dict(module.PLUGIN)
        valid, message = validate_plugin(plugin)

        plugin.setdefault("version", "")
        plugin.setdefault("author", "")
        plugin.setdefault("order", 999)
        plugin.setdefault("requires", [])

        plugin["run"] = getattr(module, "run", None)
        plugin["status"] = getattr(module, "status", None)
        plugin["commands"] = getattr(module, "commands", None)
        plugin["execute"] = getattr(module, "execute", None)
        plugin["about"] = getattr(module, "about", None)
        plugin["path"] = str(plugin_dir)
        plugin["valid"] = valid

        if not valid:
            plugin["name"] = f"❌ {plugin_dir.name}"
            plugin["description"] = message

        plugins.append(plugin)

    return sorted(plugins, key=lambda p: p.get("order", 999))

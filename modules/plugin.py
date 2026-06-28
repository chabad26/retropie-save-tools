from pathlib import Path
import importlib.util
import sys

PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugins"


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

        # Rend le dossier importable comme un package.
        if not init_file.exists():
            init_file.write_text("", encoding="utf-8")

        package_name = f"retropie_plugin_{plugin_dir.name}"

        spec = importlib.util.spec_from_file_location(
            f"{package_name}.plugin",
            plugin_file,
            submodule_search_locations=[str(plugin_dir)],
        )

        module = importlib.util.module_from_spec(spec)
        sys.modules[f"{package_name}.plugin"] = module
        sys.modules[package_name] = module

        try:
            spec.loader.exec_module(module)
        except Exception as exc:
            plugins.append({
                "id": plugin_dir.name,
                "name": f"❌ {plugin_dir.name}",
                "description": f"Erreur de chargement : {exc}",
                "version": "",
                "author": "",
                "order": 999,
                "run": None,
                "path": str(plugin_dir),
            })
            continue

        if hasattr(module, "PLUGIN"):
            plugin = dict(module.PLUGIN)
            plugin["run"] = getattr(module, "run", None)
            plugin["status"] = getattr(module, "status", None)
            plugin["path"] = str(plugin_dir)
            plugin["requires"] = plugin.get("requires", [])
            plugins.append(plugin)

    return sorted(plugins, key=lambda p: p.get("order", 999))

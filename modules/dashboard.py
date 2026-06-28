from modules.plugin import discover_plugins


ICONS = {
    "ok": "🟢",
    "warning": "🟡",
    "error": "🔴",
    "info": "🔵",
    "unknown": "⚪",
}


def plugin_status(plugin):
    fn = plugin.get("status")

    if not callable(fn):
        return {
            "state": "unknown",
            "title": plugin.get("name", plugin.get("id", "Plugin")),
            "message": "Aucun status()",
        }

    try:
        data = fn()
    except Exception as exc:
        return {
            "state": "error",
            "title": plugin.get("name", plugin.get("id", "Plugin")),
            "message": f"Erreur status : {exc}",
        }

    return {
        "state": data.get("state", "unknown"),
        "title": data.get("title", plugin.get("name", plugin.get("id", "Plugin"))),
        "message": data.get("message", ""),
    }


def text():
    plugins = discover_plugins()
    rows = [plugin_status(p) for p in plugins]

    counts = {
        "ok": sum(1 for r in rows if r["state"] == "ok"),
        "warning": sum(1 for r in rows if r["state"] == "warning"),
        "error": sum(1 for r in rows if r["state"] == "error"),
        "info": sum(1 for r in rows if r["state"] == "info"),
        "unknown": sum(1 for r in rows if r["state"] == "unknown"),
    }

    lines = []
    lines.append("RetroPie Toolbox")
    lines.append("")
    lines.append(f"Plugins chargés : {len(plugins)}")
    lines.append(
        f"🟢 {counts['ok']}   🟡 {counts['warning']}   🔴 {counts['error']}   🔵 {counts['info']}   ⚪ {counts['unknown']}"
    )
    lines.append("")
    lines.append("État des plugins")
    lines.append("────────────────")
    lines.append("")

    for row in rows:
        icon = ICONS.get(row["state"], "⚪")
        lines.append(f"{icon} {row['title']}")
        if row["message"]:
            lines.append(f"   {row['message']}")

    return "\n".join(lines)

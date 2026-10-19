"""Install the community plugins this vault lists, and seed the settings that matter.

    python .claude/scripts/install_plugins.py            # into this vault
    python .claude/scripts/install_plugins.py <vault>    # into another vault

Reads `.obsidian/community-plugins.json`, resolves each id to its GitHub repo via
Obsidian's official registry, downloads the latest release's main.js / manifest.json /
styles.css into `.obsidian/plugins/<id>/`. Skips plugins already installed.

Seeds only structural/look-and-feel settings (template folders, folder icons), and only where the plugin has
no data.json yet. Secrets (Google OAuth, API keys) are never written: enter them in the
app.
"""

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

REGISTRY = "https://raw.githubusercontent.com/obsidianmd/obsidian-releases/master/community-plugins.json"
RELEASE = "https://github.com/%s/releases/latest/download/%s"


def seed_for(vault, plugin_id):
    """Published settings for this plugin (written by publish_setup.py), or None."""
    seed_file = vault / ".claude/seeds" / (plugin_id + ".json")
    return seed_file.read_text(encoding="utf-8") if seed_file.is_file() else None


def fetch(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read()


def install(plugin_id, repo, target):
    target.mkdir(parents=True, exist_ok=True)
    for name, required in (("main.js", True), ("manifest.json", True), ("styles.css", False)):
        try:
            (target / name).write_bytes(fetch(RELEASE % (repo, name)))
        except urllib.error.HTTPError:
            if required:
                raise


def main():
    vault = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[2])
    ids = json.loads((vault / ".obsidian/community-plugins.json").read_text(encoding="utf-8"))
    registry = {p["id"]: p["repo"] for p in json.loads(fetch(REGISTRY))}

    for plugin_id in ids:
        target = vault / ".obsidian/plugins" / plugin_id
        if (target / "main.js").exists():
            print("have     ", plugin_id)
        elif plugin_id not in registry:
            print("NOT IN REGISTRY", plugin_id, "- install by hand")
        else:
            install(plugin_id, registry[plugin_id], target)
            print("installed", plugin_id, "<-", registry[plugin_id])

        data = target / "data.json"
        seed = seed_for(vault, plugin_id)
        if seed and target.is_dir() and not data.exists():
            data.write_text(seed, encoding="utf-8")
            print("seeded   ", plugin_id)


if __name__ == "__main__":
    main()

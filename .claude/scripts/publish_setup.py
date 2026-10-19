"""Stage the shareable half of this vault for the public setup repo.

    python .claude/scripts/publish_setup.py <dest>      # stage, print manifest
    python .claude/scripts/publish_setup.py <dest> -q   # stage quietly

Copies ONLY what ALLOW matches. The allowlist is the trust boundary: a denylist
fails open, because the day a new private folder appears it ships. DENY is a
second net that asserts, not a filter, so a mistake in ALLOW crashes here rather
than surfacing on github.com.

Notes never travel. Structure, templates, bases and config do.
"""

import json
import re
import shutil
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parents[2]

# Only these reach the public repo.
ALLOW = [
    "CLAUDE.md",
    ".claude/settings.json",
    ".claude/skills/**/*.md",
    ".claude/scripts/*.py",
    ".claude/scripts/*.cmd",
    # Source of the vault's own plugins (not in Obsidian's registry);
    # install_plugins.py copies them into .obsidian/plugins/.
    ".claude/plugins/*/*",
    ".claude/docs/agents/*.md",
    "System/Templates/*.md",
    "System/Plugins.md",
    "System/Tags.md",
    # Bases only, never hub/note .md. Projects/Archive is excluded by DENY.
    "Essentials/**/*.base",
    "Projects/**/*.base",
    "Notes/*.base",
    "Excalidraw/*.base",
    # Obsidian config, file by file. Never .obsidian/plugins/** - plugin data.json
    # holds the Google OAuth client secret and refresh token.
    ".obsidian/app.json",
    ".obsidian/core-plugins.json",
    ".obsidian/community-plugins.json",
    ".obsidian/daily-notes.json",
    ".obsidian/templates.json",
    ".obsidian/bookmarks.json",
    ".obsidian/hotkeys.json",
    ".obsidian/appearance.json",
    ".obsidian/snippets/*.css",
    ".obsidian/themes/*/*",
    ".obsidian/graph.json",
    ".obsidian/canvas.json",
    ".obsidian/backlink.json",
    ".obsidian/types.json",
    ".obsidian/webviewer.json",
]

# Plugin settings to publish as .claude/seeds/<id>.json (DENY keeps .obsidian/plugins/
# out wholesale because data.json can hold OAuth secrets). install_plugins.py writes
# each back as the plugin's data.json on a fresh machine.
#   "drop": publish everything except these keys (plugins whose config is all benign)
#   "keep": publish only these keys (plugins that also hold accounts or private paths)
# Both fail closed: seed_is_clean() refuses any secret-looking key with a value.
SEED_PLUGINS = {
    "obsidian-icon-folder": {},
    "pomodoro-timer": {},
    "dataview": {},
    "obsidian-kanban": {},
    "folder-notes": {},
    "obsidian-excalidraw-plugin": {"drop": ["taskboneAPIkey"]},
    "templater-obsidian": {"drop": ["shell_path", "enabled_templates_hotkeys"]},
    "obsidian-book-search-plugin": {"drop": ["apiKey", "naverClientId", "naverClientSecret"]},
    "obsidian-languagetool-plugin": {"drop": ["apikey", "username"]},
    "obsidian-tts": {"drop": ["services"]},
    "compact-pinned-tabs": {"drop": ["savedPinnedTabs"]},
    # Profiles hold machine-specific shell paths; the plugin regenerates its defaults.
    "terminal": {"drop": ["profiles"]},
    # history/previews list private note paths.
    "doomscroll": {"keep": ["settings"]},
    # Google/Microsoft accounts, tokens, location, calendar ids stay home.
    "full-calendar-remastered": {"keep": [
        "firstDay", "initialView", "timeFormat24h", "clickToCreateEventFromMonthView",
        "enableAdvancedCategorization", "enableBackgroundEvents", "enableReminders",
        "enableDefaultReminder", "defaultReminderMinutes", "businessHours",
        "slotMinTime", "slotMaxTime", "allDaySlot", "timeGridDayHeaderFormat",
        "weekends", "hiddenDays", "dayMaxEvents", "enableLivePreview",
    ]},
    # savedGroups names the owner's projects and leaf ids that mean nothing elsewhere.
    "tab-groups": {"keep": ["language", "groupStyle"]},
}
SECRET_KEY = re.compile(r"(token|secret|api_?key|password|refresh|cookie)", re.I)


def seed_is_clean(node):
    """True if no secret-looking key anywhere in `node` carries a non-empty string."""
    if isinstance(node, dict):
        return all(
            not (SECRET_KEY.search(k) and isinstance(v, str) and v) and seed_is_clean(v)
            for k, v in node.items())
    if isinstance(node, list):
        return all(seed_is_clean(v) for v in node)
    return True


def seed_data(plugin_id, rule):
    data = json.loads((VAULT / ".obsidian/plugins" / plugin_id / "data.json").read_text(encoding="utf-8"))
    if "keep" in rule:
        data = {k: v for k, v in data.items() if k in rule["keep"]}
    else:
        data = {k: v for k, v in data.items() if k not in rule.get("drop", [])}
    assert seed_is_clean(data), "seed for %s carries a secret-looking value" % plugin_id
    return data


# Nothing matching these may ever appear in the manifest. Asserted, not filtered.
DENY = [
    "Journal/",
    "Sources/",
    "Inbox/",
    "Projects/Archive/",
    "System/Specs/",
    "System/Backlog.md",
    "System/Index.md",
    "System/Hot.md",
    ".obsidian/plugins/",
    ".claudian/",
    ".git/",
]

# Skipped quietly where a broad ALLOW glob crosses a DENY folder. DENY still asserts.
EXCLUDE = ["Projects/Archive/"]

# Words that must not leave the vault. They live in a file that is itself NOT in ALLOW,
# so this script can name the mechanism without naming the words. Values are the
# replacements written into published copies; a final scan fails if any word survives.
PRIVATE_WORDS_FILE = VAULT / ".claude/private-words.json"
TEXT_SUFFIXES = {".md", ".py", ".cmd", ".js", ".json", ".base", ".css", ".txt", ".canvas", ".yml", ".yaml"}


def load_private_words():
    if not PRIVATE_WORDS_FILE.is_file():
        return {}
    words = json.loads(PRIVATE_WORDS_FILE.read_text(encoding="utf-8"))
    words.pop("_comment", None)
    return dict(sorted(words.items(), key=lambda kv: -len(kv[0])))  # longest first


def redact(path, words):
    text = path.read_text(encoding="utf-8")
    for word, replacement in words.items():
        text = re.sub(re.escape(word), replacement, text, flags=re.I)
    path.write_text(text, encoding="utf-8", newline="")


def assert_no_private_words(dest, words):
    for path in dest.rglob("*"):
        if ".git" in path.relative_to(dest).parts:
            continue
        haystack = [path.relative_to(dest).as_posix()]
        if path.is_file() and path.suffix in TEXT_SUFFIXES:
            haystack.append(path.read_text(encoding="utf-8", errors="ignore"))
        for word in words:
            assert not any(word.lower() in h.lower() for h in haystack), (
                "private word survived in %s" % path.relative_to(dest))


# Folders that exist only to show the shape. Empty in the public repo.
SKELETON = [
    "Notes",
    "Projects",
    "Essentials",
    "Journal",
    "Sources",
    "Inbox",
    "System/Attachments",
    "System/Specs",
    "Excalidraw",
]


def denied(rel):
    return next((d for d in DENY if rel.replace("\\", "/").startswith(d)), None)


def sanitise_settings(path):
    """Drop `permissions.allow` from the published settings.json.

    The deny rules are the point of that file: they are what write-protects the
    journal, and they are what someone reading this repo wants to copy. The allow
    list is the opposite - one-off Bash commands accumulated from past sessions,
    which happen to carry an email address and the filenames of personal notes.
    Stripped on every publish rather than once by hand, so it cannot come back.
    """
    settings = json.loads(path.read_text(encoding="utf-8"))
    settings.get("permissions", {}).pop("allow", None)
    path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")

    leaked = [w for w in ("@", "Obsidian\\\\", "git config") if w in path.read_text(encoding="utf-8")]
    assert not leaked, "settings.json still carries %s" % leaked


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    dest = Path(sys.argv[1]).resolve()
    quiet = "-q" in sys.argv

    words = load_private_words()
    staged = []
    for pattern in ALLOW:
        for src in sorted(VAULT.glob(pattern)):
            if not src.is_file():
                continue
            rel = str(src.relative_to(VAULT))
            if rel.replace("\\", "/").startswith(tuple(EXCLUDE)):
                continue
            if any(w.lower() in rel.lower() for w in words):
                continue  # a path that names a private word is skipped, not renamed
            hit = denied(rel)
            assert hit is None, "ALLOW pattern %r leaked a DENY path: %s (matched %r)" % (
                pattern, rel, hit)
            out = dest / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, out)
            if out.suffix in TEXT_SUFFIXES:
                redact(out, words)
            staged.append(rel)

    for plugin_id, rule in SEED_PLUGINS.items():
        if not (VAULT / ".obsidian/plugins" / plugin_id / "data.json").is_file():
            continue
        out = dest / ".claude/seeds" / (plugin_id + ".json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(seed_data(plugin_id, rule), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        staged.append(str(out.relative_to(dest)))

    for out in (dest / ".claude/seeds").glob("*.json"):
        redact(out, words)

    for folder in SKELETON:
        keep = dest / folder / ".gitkeep"
        keep.parent.mkdir(parents=True, exist_ok=True)
        keep.touch()

    sanitise_settings(dest / ".claude/settings.json")

    # The vault's own secret-bearing paths must not exist in dest, by any route.
    # `.git/` is excluded because dest is itself the publishing repo: its git
    # metadata is the destination's own, not something copied out of the vault.
    for d in (p for p in DENY if p != ".git/"):
        leaked = sorted(p for p in (dest / d).rglob("*") if p.is_file()) if (dest / d).is_dir() else []
        leaked = [p for p in leaked if p.name != ".gitkeep"]
        assert not leaked, "DENY path present in staging: %s" % leaked[:3]

    assert_no_private_words(dest, words)

    if not quiet:
        for rel in staged:
            print(rel)
    print("\n%d files, %d skeleton folders -> %s" % (len(staged), len(SKELETON), dest))


if __name__ == "__main__":
    main()

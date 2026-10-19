"""Every hard-coded vault path in config, scripts and bases - does it still exist?

    python .claude/scripts/check_paths.py        # exits 1 if any path is dead

Run BEFORE a folder rename to record the baseline, and AFTER to prove nothing was
missed. Obsidian updates wikilinks on a UI rename; it does NOT update `.base`
filters, `newItemFolder`, `daily-notes.json`, Templater path constants, or the
journal deny rules in `.claude/settings.json`. A dead base filter shows an empty
view and raises no error, which is why this has to be checked rather than noticed.
"""

import json
import re
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parents[2]
TOP = ("The Core", "Projects", "System", "Excalidraw")
# A quoted string that starts at a (optionally numbered) top-level folder.
PATH = re.compile(r'["\']((?:\d+\s+)?(?:%s)(?:/[^"\'\n*?<>|]+)*)["\']'
                  % "|".join(re.escape(name) for name in TOP))
SOURCES = [".claude/settings.json", ".claude/scripts", ".claude/skills",
           ".claude/docs", ".obsidian/daily-notes.json", ".obsidian/templates.json",
           ".obsidian/app.json"]
SKIP_SEGMENTS = ("_archive", ".git", "node_modules")


def candidates():
    """(file, path-like string) for every hard-coded vault path worth checking."""
    files = [VAULT / s for s in SOURCES]
    files += [p for p in VAULT.rglob("*.base") if "_archive" not in str(p)]

    for entry in files:
        for path in ([entry] if entry.is_file() else sorted(entry.rglob("*"))):
            if (not path.is_file() or path == Path(__file__).resolve()
                    or any(s in str(path) for s in SKIP_SEGMENTS)):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for match in PATH.finditer(text):
                yield path.relative_to(VAULT), match.group(1)


def main():
    dead, seen = [], set()
    for source, target in candidates():
        if (source, target) in seen:
            continue
        seen.add((source, target))
        if "{" in target:  # an f-string template, not a path
            continue
        # A deny rule ends in /** ; strip the glob before testing the folder.
        folder = target.split("/**")[0].rstrip("/")
        if not (VAULT / folder).exists():
            dead.append((source, target))

    for source, target in sorted(dead):
        print("DEAD  %-46s  %s" % (target, source))
    print("\n%d hard-coded paths checked, %d dead." % (len(seen), len(dead)))
    return 1 if dead else 0


if __name__ == "__main__":
    sys.exit(main())

"""Phase 2 flatten: print every planned move of vault v2; `--apply` performs them.

    python .claude/scripts/flatten_plan.py            # print only
    python .claude/scripts/flatten_plan.py --apply    # git mv everything (0 collisions only)

Spec: 5 Settings/Specs/2026-10-05 Vault v2 flat layout and ingest.md, Phase 2.
Prints `old -> new` per destination, then every collision (two files landing on
one path) and every path-qualified link outside the journal. Exits 1 while a
collision remains, so it doubles as the gate before the real move.
"""

import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import PurePosixPath as P

JOURNAL = "Journal/"
STAYS = ("_archive/", ".claude/", ".obsidian/", ".claudian/", "System/", "Projects/", "Notes/",
         "Sources/", "Excalidraw/",
         "CLAUDE.md", "Home.md", ".gitignore")
# Hubs that only listed a folder's content. Their job moves to views in
# System/Bases/Notes.base, so they and their .base are archived, not moved.
FORMAT_HUBS = {"1 Fleeting Notes", "2 Permanent Notes", "3 Summaries", "Books", "Movies",
               "Podcasts", "Series", "Youtube", "Studies", "4 The Garden",
               "3 Organisations", "4 Hobbies", "Plans"}
# note_type values that mark a project/area hub.
PROJECT_TYPES = {"Hub", "Course", "Subject"}
ATTACHMENT = re.compile(r"\.(png|jpe?g|gif|svg|webp)$", re.I)
PATH_LINK = re.compile(r"!?\[\[([^\]|#]*/[^\]|#]*)")


def tracked():
    out = subprocess.run(["git", "-c", "core.quotepath=off", "ls-files"],
                         capture_output=True, text=True, encoding="utf-8", check=True)
    return out.stdout.splitlines()


def note_type(path):
    text = open(path, encoding="utf-8", errors="replace").read()
    block = re.match(r"---\r?\n(.*?)\r?\n---", text, re.S)
    found = block and re.search(r"^note_type:[ \t]*(.+?)[ \t]*\r?$", block.group(1), re.M)
    return found.group(1).strip("\"'") if found else ""


def destination(path):
    """New path for `path`, or None if it stays where it is."""
    if path.startswith(JOURNAL) or path.startswith(STAYS):
        return None
    p = P(path)
    if path.startswith("5 Settings/Templates/"):
        return f"System/Templates/{p.name}"
    if path.startswith("5 Settings/Specs/"):
        return f"System/Specs/{p.name}"
    if path.startswith("5 Settings/"):
        return f"System/{p.name}"
    if p.stem in FORMAT_HUBS and p.suffix in (".md", ".base"):
        return f"_archive/{path}"
    if p.suffix == ".base":
        return f"System/Bases/{p.name}"
    if p.suffix == ".pdf":
        return f"Sources/{p.name}"
    if ATTACHMENT.search(path):
        return f"System/Attachments/{p.name}"
    if p.suffix == ".md":
        folder = "Projects" if note_type(path) in PROJECT_TYPES else "Notes"
        return f"{folder}/{p.name}"
    return f"UNMAPPED/{path}"


def main():
    files = tracked()
    moves = {f: destination(f) for f in files}
    moves = {f: d for f, d in moves.items() if d}

    by_folder = defaultdict(list)
    for old, new in sorted(moves.items(), key=lambda m: m[1]):
        by_folder[new.split("/")[0]].append((old, new))
    for folder, rows in by_folder.items():
        print(f"\n## {folder}  ({len(rows)})")
        for old, new in rows:
            print(f"  {old}\n    -> {new}")

    # Links are bare-name, so two live files sharing a filename anywhere is a
    # collision, not just two files landing on one path. _archive/ is out of play.
    claims = defaultdict(list)
    for old in files:
        new = moves.get(old, old)
        if not new.startswith(("_archive/", ".")):
            claims[P(new).name.casefold()].append(f"{old} -> {new}" if old in moves else f"{old} (stays)")
    collisions = {name: olds for name, olds in claims.items() if len(olds) > 1}
    print(f"\n## Collisions  ({len(collisions)})")
    for new, olds in sorted(collisions.items()):
        print(f"  {new}\n" + "".join(f"    <- {o}\n" for o in olds), end="")

    print("\n## Path-qualified links outside the journal")
    for f in files:
        if f.endswith(".md") and not f.startswith((JOURNAL, "_archive/", ".claude/")):
            for n, line in enumerate(open(f, encoding="utf-8", errors="replace"), 1):
                for target in PATH_LINK.findall(line):
                    print(f"  {f}:{n}  [[{target}]]")

    print(f"\n{len(moves)} moves, {len(collisions)} collisions.")
    if collisions:
        return 1
    if "--apply" in sys.argv:
        for old, new in moves.items():
            os.makedirs(P(new).parent, exist_ok=True)
            subprocess.run(["git", "mv", old, new], check=True)
        print(f"Applied {len(moves)} moves.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

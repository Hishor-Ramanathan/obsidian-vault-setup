"""Report structural drift in the vault. Reads only - never renames or writes.

    python .claude/scripts/tidy.py              # all checks
    python .claude/scripts/tidy.py --orphans    # + inbound-link scan (slow)

Every check here corresponds to a verification the vault's CLAUDE.md already asks
for after a restructure. The point is that they run in one command instead of from
memory, and that the journal is inspected without being touched.
"""

import re
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parents[2]
JOURNAL = VAULT / "Journal"
SKIP = ("_archive", ".git", ".obsidian", ".claude", ".claudian", "Pictures")

MONTHS = ("January February March April May June July August September October "
          "November December").split()

findings = []


def ignored_prefixes():
    """Folders Obsidian hides from search - and therefore from every Base.

    A Base whose folder sits under one of these renders completely empty, with
    the cause two folders away in a config file and no error anywhere. Issue #4.
    """
    import json
    config = VAULT / ".obsidian/app.json"
    if not config.exists():
        return ()
    raw = json.loads(config.read_text(encoding="utf-8")).get("userIgnoreFilters", [])
    return tuple(f.strip("/") for f in raw if not f.startswith("/"))


IGNORED = ignored_prefixes()


POSITIVE_FOLDER = re.compile(
    r'(?P<not>!?)\s*(?:file\.)?(?:inFolder|containsAll)\(\s*"(?P<path>[^"]+)"')


def flag_ignored_targets(rel, text):
    """A Base that *selects* a hidden folder renders empty, with no error anywhere.

    Only positive filters matter. `!file.inFolder("5 Settings")` excludes a folder
    that is already hidden - redundant, not broken.
    """
    for match in POSITIVE_FOLDER.finditer(text):
        if match.group("not"):
            continue
        target = match.group("path")
        if any(target == h or target.startswith(h + "/") for h in IGNORED):
            note("base-in-ignored-folder",
                 "%s -> %s (hidden by userIgnoreFilters)" % (rel, target))


def note(check, detail):
    findings.append((check, detail))


def notes():
    """Every markdown note outside the skip list."""
    for p in VAULT.rglob("*.md"):
        rel = p.relative_to(VAULT).as_posix()
        if not any(part in SKIP for part in rel.split("/")):
            yield p, rel


def check_journal_names():
    """Month and week folders must be zero-padded, English, and `<N> Week`.

    Unpadded numbers sort as text, so `10 October` lands before `9 September` and
    `3 Week` after `28 Week`. The pattern matters beyond looks: the daily template
    dispatches on /^\\d{1,2}\\s+Week$/i, so a folder named `Week 10` gets no weekly
    template at all and the weekly review silently never generates.
    """
    for year in sorted(p for p in JOURNAL.glob("[0-9][0-9][0-9][0-9]") if p.is_dir()):
        for month in sorted(p for p in year.iterdir() if p.is_dir()):
            m = re.match(r"^(\d{1,2}) (\S+)$", month.name)
            if not m:
                note("journal-month", "unrecognised: %s" % month.name)
                continue
            num, name = m.groups()
            if len(num) == 1:
                note("journal-pad", "%s -> %s" % (month.name, "0" + month.name))
            if name not in MONTHS:
                note("journal-lang", "%s is not English (locale drift)" % month.name)

            for week in sorted(p for p in month.iterdir() if p.is_dir()):
                if re.match(r"^Week (\d{1,2})$", week.name):
                    n = week.name.split()[1]
                    note("journal-week-pattern",
                         "%s/%s -> %s Week  (no weekly template applied)"
                         % (month.name, week.name, n.zfill(2)))
                elif re.match(r"^(\d{1,2}) Week$", week.name):
                    n = week.name.split()[0]
                    if len(n) == 1:
                        note("journal-pad", "%s/%s -> 0%s" % (month.name, week.name, week.name))
                else:
                    note("journal-week-pattern", "unrecognised: %s" % week.name)


def check_folder_notes():
    """A folder note is `<folder>/<folder>.md`. Missing or empty means a dead hub.

    Only folders that *claim* to be a section are checked, because most folders are
    not meant to have one: a folder holding a `.base` is a hub by construction, and
    a journal month or week folder is one the daily template is supposed to create.
    Checking every folder instead produced forty findings about template
    directories and attachment leaves, which is how a report teaches you to ignore
    it.
    """
    candidates = {p.parent for p in VAULT.rglob("*.base")}
    candidates |= {p for p in JOURNAL.rglob("*") if p.is_dir()}

    for folder in sorted(candidates):
        rel = folder.relative_to(VAULT).as_posix()
        if any(part in SKIP for part in rel.split("/")) or rel.startswith("System"):
            continue
        fn = folder / (folder.name + ".md")
        if not fn.exists():
            note("folder-note-missing", rel)
        elif fn.stat().st_size < 20:
            note("folder-note-empty", "%s (%d bytes)" % (rel, fn.stat().st_size))


def check_frontmatter():
    """Frontmatter must parse, and non-journal notes should carry note_type.

    A block whose closing `---` was eaten stops being frontmatter at all, and the
    note then vanishes from every Base that filters on a property. That has
    happened here before, via a `perl -pe` pattern ending in `\\s*$`.
    """
    for p, rel in notes():
        # Templates are config, not notes: their frontmatter is
        # generated by Templater at insertion.
        # CLAUDE.md is an instruction file that happens to end in .md.
        if rel.startswith("System/Templates/") or rel == "CLAUDE.md":
            continue
        is_journal = rel.startswith("Journal/")
        text = p.read_text(encoding="utf-8", errors="replace")
        if not text.startswith("---"):
            if not is_journal:
                note("no-frontmatter", rel)
            continue
        end = text.find("\n---", 3)
        if end == -1:
            note("frontmatter-unclosed", rel)
            continue
        block = text[3:end].strip("\n")
        for line in block.splitlines():
            if line.strip() and not re.match(r"^\s*(- |[A-Za-z_][\w -]*:)", line):
                note("frontmatter-malformed", "%s: %r" % (rel, line[:60]))
        if "note_type:" not in block and not is_journal:
            note("no-note-type", rel)


def check_bases():
    """Every path a base names must exist: newItemFolder and any inFolder()."""
    for b in VAULT.rglob("*.base"):
        rel = b.relative_to(VAULT).as_posix()
        if rel.startswith("_archive"):
            continue
        text = b.read_text(encoding="utf-8", errors="replace")
        flag_ignored_targets(rel, text)
        for m in re.finditer(r'newItemFolder:\s*"?([^"\n]+)"?', text):
            if not (VAULT / m.group(1).strip()).is_dir():
                note("base-dead-newitemfolder", "%s -> %s" % (rel, m.group(1).strip()))
        for m in re.finditer(r'(?:inFolder|containsAll)\(\s*"([^"]+)"', text):
            if not (VAULT / m.group(1)).is_dir():
                note("base-dead-path", "%s -> %s" % (rel, m.group(1)))


def check_orphans():
    """Notes nothing links to. Slow: one pass per note.

    ponytail: O(notes x notes) substring scan. Fine at this vault's size (~500
    notes, a couple of seconds). If it ever drags, build one link index instead.
    """
    all_notes = list(notes())
    corpus = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p, _ in all_notes)
    for p, rel in all_notes:
        if p.stem == "Home" or rel.startswith("System"):
            continue
        if ("[[%s" % p.stem) not in corpus:
            note("orphan", rel)


def main():
    check_journal_names()
    check_folder_notes()
    check_frontmatter()
    check_bases()
    if "--orphans" in sys.argv:
        check_orphans()

    if not findings:
        print("No drift found.")
        return

    width = max(len(c) for c, _ in findings)
    last = None
    for check, detail in findings:
        if check != last:
            print()
            last = check
        print("%-*s  %s" % (width, check, detail))
    print("\n%d findings across %d checks"
          % (len(findings), len(set(c for c, _ in findings))))


if __name__ == "__main__":
    main()

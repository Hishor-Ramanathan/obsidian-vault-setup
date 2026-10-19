"""Regenerate System/Index.md and System/Hot.md from frontmatter and git history.

    python .claude/scripts/wiki_index.py           # write both files
    python .claude/scripts/wiki_index.py --check   # parser self-check

The agent reads Index.md before writing anything, to decide "update the existing
note" vs "create a new one" (titles + aliases), and Hot.md to see what changed
recently. Both are derived: never edit them by hand, and they are git-ignored.

Names are plain text, not [[links]], on purpose: tidy.py's orphan check counts any
`[[Name` as an inbound link, so a linked index would make every note look linked.
"""

import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date

from tidy import VAULT, notes

SYSTEM = VAULT / "System"
# Not wiki content: the journal is private, the rest is config or drawings.
EXCLUDED = ("Journal/", "System/", "Excalidraw/")
HOT_SIZE = 20


@dataclass
class Note:
    """The catalogue-relevant part of one note: its name and selected properties."""
    title: str
    path: str
    note_type: str = ""
    project: str = ""
    tags: list = field(default_factory=list)
    aliases: list = field(default_factory=list)

    @classmethod
    def from_text(cls, title, path, text):
        props = Frontmatter.parse(text)
        return cls(
            title=title,
            path=path,
            note_type=props.get("note_type", ""),
            # `org:` is the pre-v2 name of `project:`; read both until it is migrated.
            project=props.get("project") or props.get("org", ""),
            tags=Frontmatter.as_list(props.get("tags")),
            aliases=Frontmatter.as_list(props.get("aliases")),
        )

    def row(self):
        cells = (self.title, self.note_type, _unlink(self.project),
                 ", ".join(self.tags), ", ".join(self.aliases), self.path)
        return "| " + " | ".join(str(c).replace("|", "\\|") for c in cells) + " |"


class Frontmatter:
    """Reads the YAML subset this vault uses: `key: value`, `key: [a, b]`, and
    `key:` followed by `- item` lines. Anything fancier is not used here, and a
    stdlib parser avoids making PyYAML a dependency of every vault script."""

    @staticmethod
    def parse(text):
        if not text.startswith("---"):
            return {}
        end = text.find("\n---", 3)
        if end == -1:
            return {}
        props, key = {}, None
        for line in text[3:end].splitlines():
            item = re.match(r"^\s*-\s+(.*)$", line)
            if item and key:
                props.setdefault(key, [])
                if isinstance(props[key], list):
                    props[key].append(_unquote(item.group(1)))
                continue
            pair = re.match(r"^([A-Za-z_][\w -]*):\s*(.*)$", line)
            if pair:
                key, value = pair.group(1).strip(), pair.group(2).strip()
                if value.startswith("[") and value.endswith("]"):
                    props[key] = [_unquote(v) for v in value[1:-1].split(",") if v.strip()]
                elif value:
                    props[key] = _unquote(value)
        return props

    @staticmethod
    def as_list(value):
        if not value:
            return []
        return value if isinstance(value, list) else [value]


class Catalog:
    """Every wiki note in the vault, and the two derived files built from them."""

    def __init__(self):
        self.notes = sorted(
            (Note.from_text(p.stem, rel, p.read_text(encoding="utf-8", errors="replace"))
             for p, rel in notes()
             if rel.endswith(".md") and rel != "CLAUDE.md" and not rel.startswith(EXCLUDED)),
            key=lambda n: n.title.lower())
        self.by_path = {n.path: n for n in self.notes}

    def write_index(self):
        lines = [_header("Every note: name, kind, project, tags, aliases. Look up a "
                         "term against Note *and* Aliases before creating a note."),
                 "| Note | Type | Project | Tags | Aliases | Path |",
                 "|---|---|---|---|---|---|"]
        lines += [n.row() for n in self.notes]
        (SYSTEM / "Index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def write_hot(self):
        recent = list(self._recent_changes())
        lines = [_header("The %d most recently changed notes, newest first, from git "
                         "history." % HOT_SIZE),
                 "| Changed | Note | Type | Commit |",
                 "|---|---|---|---|"]
        for day, subject, path in recent:
            n = self.by_path[path]
            lines.append("| %s | %s | %s | %s |" % (day, n.title, n.note_type,
                                                    subject.replace("|", "\\|")))
        (SYSTEM / "Hot.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _recent_changes(self):
        log = subprocess.run(
            ["git", "-c", "core.quotePath=false", "log", "--name-only",
             "--date=short", "--format=\x01%ad\x02%s", "-n", "200"],
            cwd=VAULT, capture_output=True, text=True, encoding="utf-8", check=True).stdout
        seen = set()
        for commit in log.split("\x01")[1:]:
            head, *paths = commit.strip().splitlines()
            day, subject = head.split("\x02", 1)
            for path in paths:
                if path in self.by_path and path not in seen:
                    seen.add(path)
                    yield day, subject, path
                    if len(seen) == HOT_SIZE:
                        return


def _header(purpose):
    return ("---\nnote_type: System\nsource: claude\n---\n"
            "Generated %s by `.claude/scripts/wiki_index.py`. Do not edit: it is "
            "rewritten on every run.\n\n%s\n" % (date.today().isoformat(), purpose))


def _unquote(value):
    return value.strip().strip("'\"")


def _unlink(value):
    return value.replace("[[", "").replace("]]", "")


def _check():
    text = ('---\nnote_type: Concept\nproject: "[[ExampleProject]]"\ntags: [topic/ai, format/book]\n'
            'aliases:\n  - Spacing Effect\n  - "Verteilte Wiederholung"\n---\nbody\n')
    n = Note.from_text("Spaced Repetition", "Notes/Spaced Repetition.md", text)
    assert n.note_type == "Concept", n
    assert n.project == "[[ExampleProject]]", n
    assert n.tags == ["topic/ai", "format/book"], n
    assert n.aliases == ["Spacing Effect", "Verteilte Wiederholung"], n
    assert n.row().startswith("| Spaced Repetition | Concept | ExampleProject |"), n.row()
    assert Note.from_text("Bare", "Bare.md", "no frontmatter").note_type == ""
    print("ok")


if __name__ == "__main__":
    if "--check" in sys.argv:
        _check()
    else:
        SYSTEM.mkdir(exist_ok=True)
        catalog = Catalog()
        catalog.write_index()
        catalog.write_hot()
        print("Index: %d notes. Hot: %d." % (len(catalog.notes),
              (SYSTEM / "Hot.md").read_text(encoding="utf-8").count("\n| 20")))

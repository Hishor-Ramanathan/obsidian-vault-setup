"""Habit consistency, read straight from the daily notes. Read-only.

    python .claude/scripts/habits.py             # last 30 days, worst first
    python .claude/scripts/habits.py --days 14
    python .claude/scripts/habits.py --json
    python .claude/scripts/habits.py --selftest

Daily notes carry no reliable `created:` frontmatter (17 of 143 have one), and
adding it is forbidden by CLAUDE.md, so the DD.MM.YYYY filename is the date.

A day the habit never appeared on is neither kept nor broken - it is skipped.
Physical Activity is offered daily now, but was Mon/Wed/Fri as `Gym`, so the
old entries would otherwise score 3/7 every week.
"""

import json
import re
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

JOURNAL = Path(__file__).resolve().parents[2] / "Journal"
DAILY_NAME = re.compile(r"^(\d{2})\.(\d{2})\.(\d{4})$")
CHECKBOX = re.compile(
    r"^[ \t]*- \[(?P<mark>.)\][ \t]+(?P<name>[^\s][^\r\n]*?)[ \t]*$", re.M)
# `[ \t]`, never `\s`: `\s` crosses the newline after an empty `- [ ] ` and
# swallows the whole next line as a habit name.
MIN_APPEARANCES = 3  # below this it is a one-off to-do, not a habit

# Renamed habits keep their history. The journal is write-protected, so old entries
# still say "Gym" forever and folding has to happen on read.
ALIASES = {"Gym": "Physical Activity"}


def read_ledger(journal=JOURNAL):
    """date -> {habit: kept}, over every daily note in the journal."""
    ledger = defaultdict(dict)
    for path in journal.rglob("*.md"):
        stamp = DAILY_NAME.match(path.stem)
        if not stamp:
            continue
        day, month, year = (int(part) for part in stamp.groups())
        text = path.read_text(encoding="utf-8", errors="replace")
        for box in CHECKBOX.finditer(text):
            name = ALIASES.get(box.group("name"), box.group("name"))
            kept = box.group("mark").lower() == "x"
            entry = ledger[date(year, month, day)]
            entry[name] = entry.get(name, False) or kept
    return ledger


def score(ledger, window, today=None):
    """Per habit: appearances, kept, current streak, best run - worst first."""
    today = today or date.today()
    days = [today - timedelta(days=n) for n in reversed(range(window))]

    stats = {}
    for habit in {h for day in days for h in ledger.get(day, {})}:
        marks = [(day, ledger[day][habit]) for day in days if habit in ledger.get(day, {})]
        if len(marks) < MIN_APPEARANCES:
            continue

        streak, live, best, run = 0, True, 0, 0
        for _, kept in reversed(marks):
            if kept and live:
                streak += 1
            elif not kept:
                live = False
        for _, kept in marks:
            run = run + 1 if kept else 0
            best = max(best, run)

        stats[habit] = {
            "offered": len(marks),
            "kept": sum(kept for _, kept in marks),
            "streak": streak,
            "best": best,
            "last_kept": max((d.isoformat() for d, k in marks if k), default=None),
        }

    return dict(sorted(stats.items(), key=lambda kv: kv[1]["kept"] / kv[1]["offered"]))


def selftest():
    ledger = {
        date(2026, 9, 10): {"Meditate": False, "Physical Activity": True},
        date(2026, 9, 11): {"Meditate": False, "Physical Activity": True},
        date(2026, 9, 12): {"Meditate": False, "Physical Activity": True},
    }
    stats = score(ledger, window=7, today=date(2026, 9, 12))
    assert list(stats) == ["Meditate", "Physical Activity"], "worst habit must sort first"
    assert stats["Meditate"] == {"offered": 3, "kept": 0, "streak": 0, "best": 0,
                                 "last_kept": None}
    assert stats["Physical Activity"]["streak"] == 3
    assert stats["Physical Activity"]["best"] == 3
    assert score(ledger, window=7, today=date(2026, 9, 12)).get("Skipped") is None
    print("selftest ok")


def main():
    if "--selftest" in sys.argv:
        return selftest()

    window = 30
    if "--days" in sys.argv:
        window = int(sys.argv[sys.argv.index("--days") + 1])

    stats = score(read_ledger(), window)
    if "--json" in sys.argv:
        print(json.dumps({"window_days": window, "habits": stats}, indent=2))
        return

    print("Last %d days, worst first:\n" % window)
    for habit, s in stats.items():
        print("  %-34s %3d%%  %2d/%-2d  streak %-2d  best %-2d  last %s"
              % (habit, round(100 * s["kept"] / s["offered"]), s["kept"], s["offered"],
                 s["streak"], s["best"], s["last_kept"] or "never"))
    if not stats:
        print("  no habit appeared %d+ times in the window." % MIN_APPEARANCES)


if __name__ == "__main__":
    main()

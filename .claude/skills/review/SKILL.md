---
name: review
description: Weekly review - one status line per area, then what slipped. Use when the user asks for a weekly review, how the week went, "where am I", a status check across projects, or invokes /review.
---

# Review

The week, one line per area, then the honest part. `/consult` answers *what to read*;
this answers *where things stand*. It does not replace `/consult`.

## The areas

Fixed, and in this order. A status line for each, every time - an area with no
movement is itself the finding:

| Area | Where to look |
|---|---|
| Siemens | `Projects/` hubs and their `project:` notes, the `Siemens` task list |
| FHNW | `Projects/` course hubs (`note_type: Course`/`Subject`), the `FHNW` task list, exam events |
| ExampleProject | `Projects/ExampleProject.md` and notes with `project: "[[ExampleProject]]"`, the `ExampleProject` task list |
| Body | `#### Goals` checkboxes in the daily notes - via `habits.py`, not by eye |
| Money | finance notes in `Notes/`, the `Personal` task list |

## Steps

1. **Current state first**, the `/consult` pattern: the last 7-14 daily entries in
   `Journal/<year>/<month>/<week>/DD.MM.YYYY.md`.
   **Read-only - never edit the journal.** Entries are English/German mixed.

2. **Habits, measured not guessed.** `python .claude/scripts/habits.py --days 7`.
   Percentages and streaks come from there. Never estimate them from reading.

3. **Tasks.** `python .claude/scripts/tasks.py` - what closed, what is still open per
   list. Only tasks say what was finished; the journal says what it felt like.

4. **Calendar, for what was actually committed to.** `list_events` for the past week,
   `timeZone: Europe/Zurich`.

5. **Signals.** `python .claude/scripts/nudge.py --all --dry-run`. Same ranking as
   `/brief`, one model.

## Output

One line per area, then one short block:

```
Siemens    <what moved, or "nothing since <date>">
FHNW       ...
ExampleProject   ...
Body       Deep Work 3/7, Meditate 0/7 - last logged <date>
Money      ...

Slipped    <the one thing that keeps not happening, named, with dates>
```

## Rules

- **One** thing under `Slipped`. A list of five is a way of not choosing.
- Dates, not adjectives. "Last logged 2026-08-10" beats "has been inconsistent".
- Do not be agreeable. A review that reports a good week when three habits are at 0%
  is worthless. If the week was genuinely good, say so in one line and move on.
- Do not write the review into a note unless asked. If asked, it is a **new** note
  in `Notes/`, carrying `source: claude` and linking back.
- Do not schedule this yet - same reason as `/brief`.

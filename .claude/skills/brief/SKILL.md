---
name: brief
description: What today actually holds - calendar, open tasks, mail from real humans, and what yesterday's note said would happen. Use when the user asks what is on today, for a morning brief, "what do I have today", "brief me", or invokes /brief.
---

# Brief

Today, from live sources. Read the state, never the vault's memory of the state.

## Steps

1. **Calendar.** `list_events` over every calendar `list_calendars` returns.
   **Always pass `timeZone: Europe/Zurich`.** The FHNW and `Familie` calendars are
   UTC, and all-day events shift a day without it. FHNW is `accessRole: reader` -
   never attempt a write there.

2. **Tasks.** `python .claude/scripts/tasks.py`. One list per area (FHNW, Siemens,
   ExampleProject, Personal), which is why the split is not re-derived from title prefixes.
   Read-only: deadlines are entered by hand in Google Tasks, not by this skill.

3. **Mail - by query, never by scanning.** ~17k messages, ~8.8k unread, roughly 90%
   of recent traffic LinkedIn notifications. Filter *inside* the search, so the
   landfill is never read and discarded:

   ```
   newer_than:2d -from:linkedin.com -category:promotions -category:social -label:Newsletter
   ```

   Then keep only what a person wrote to him. A thread that needs an answer is the
   finding; a thread that merely arrived is not. If nothing qualifies, say "no mail
   worth answering" - do not pad.

4. **Yesterday.** `Journal/<year>/<month>/<week>/DD.MM.YYYY.md`
   for yesterday. Read the `#### Goals` and `#### To Dos` boxes: what was promised,
   what is still unticked. **Read-only - never edit the journal.**

5. **Signals.** `python .claude/scripts/nudge.py --all --dry-run`. Reuse that ranking.
   Do not invent a second signal model; if the ranking is wrong, fix `nudge.py`.

## Output

Six lines, maximum. In this order:

```
Today      <the two or three things with a time attached>
Due        <tasks actually close, not the whole list>
Reply      <threads from humans awaiting an answer>
Carried    <yesterday's unticked To Dos>
Slipping   <the top nudge.py signal, if any>
```

Drop any line that has nothing in it. An empty line printed as "nothing" is noise,
and a brief that always looks the same gets muted - which is the failure mode this
whole rail exists to avoid.

## Rules

- **Do not schedule this.** Run it by hand for a week first. A morning brief that
  fires before a single one has been read is a notification that gets ignored.
  Wire it to the nudge rail (`nudge.py`) only once the shape has survived a week.
- Do not write today's daily note, or tick anything in it. Reporting only.
- Do not send mail from here. `/brief` reads; sending is a separate, deliberate act.
- Name what slipped. The vault's working agreement: the useful answer is the one
  that says what is being avoided, not the one that summarises what is already there.

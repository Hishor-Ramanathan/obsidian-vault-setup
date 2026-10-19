---
name: nudge
description: Name the habit that is slipping and ask why, using the daily notes as evidence. Use when the user asks how consistent they have been, why they stopped a habit, for a habit check-in, or invokes /nudge.
---

# Nudge

Ask the question the owner is avoiding. One habit, one question, grounded in dates.

The vault's working agreement says *"Do not be agreeable… the useful answer is the one
that names what is being avoided."* A nudge that congratulates is worthless.

## Steps

1. Run both windows — the gap between them is usually the story:

   ```
   python .claude/scripts/habits.py --days 14
   python .claude/scripts/habits.py --days 90
   ```

   `offered` is how many days the checkbox appeared; `kept` is how many were ticked. A
   habit that never appears is not being neglected — it was dropped from the template.

2. **An empty checkbox means no record, not "did not happen".** He does the gym and
   meditates without ticking anything. Never tell him he stopped doing something —
   ask whether it happened. Absence only becomes evidence once a passive source
   (phone, Health Connect) is feeding the vault.

3. Pick **one** habit: the worst 14-day record that has a non-zero 90-day record.
   If every habit is empty in both windows, the subject is not the habit — it is that
   the vault cannot see anything he does away from a desk. Say that instead, and treat
   it as a tooling problem, not a discipline problem.

4. Read the last 7 daily notes for what changed around the date in `last_kept`. The
   journal is readable. Look for what replaced the habit — a deadline, a trip, illness,
   a new project — do not invent a cause.

5. Ask. Two or three sentences, no preamble:
   - the number, with its date: *"Meditate: 1 of 14, last ticked 10 August."*
   - what the journal shows changed around then, if anything
   - one direct question — *"Did you do it?"*, not *"why did you stop?"* — then **stop talking**

## Rules

- **Never edit the journal.** Read only. `Edit`/`Write` are denied on it and that is
  deliberate.
- No streak emoji, no encouragement, no "great job on X". If something is going well,
  one clause at most.
- One habit per nudge. Three questions is a report, and a report gets skimmed.
- Never guess a cause the journal does not support. "I don't see what changed" is a
  legitimate thing to say, and it makes the question sharper.

---
name: tidy
description: Check the vault for structural drift and propose fixes. Use when the user asks to clean up the vault, asks why the folder structure is messed up, asks whether anything is broken, before or after a restructure, or invokes /tidy.
---

# Tidy

Find what has drifted, say what it costs, propose the renames. **Report first, change
nothing until told.**

The script reads only. It never renames, moves or writes, so it is safe to run on the
journal, which it inspects but must never touch.

## Steps

1. **Run it.**

   ```
   python .claude/scripts/tidy.py            # all checks
   python .claude/scripts/tidy.py --orphans  # + notes nothing links to (slow)
   ```

2. **Read the tree state before proposing anything.** `git status --short`. If the
   tree is dirty, say so and stop: CLAUDE.md requires a clean tree before a
   restructure, because one `git revert` has to be able to undo the whole thing.

3. **Group the findings by what they cost**, not by count. A class of 20 findings
   that changes nothing is worth one line; a single finding that hides a note from
   every Base is worth a paragraph. See the table below.

4. **Propose renames as a list, never as a diff of 200 files.** CLAUDE.md: *propose
   before you move*. Anything over about five files gets described and waits for
   explicit approval.

5. **Never execute inside `Journal/`.** `Edit` and `Write` are
   denied there by `.claude/settings.json`, and `mv`/`cp` are forbidden by CLAUDE.md.
   Journal folder renames are the owner's to run in the Obsidian UI (F2), which also
   keeps `alwaysUpdateLinks` in charge of any embeds. Output the exact list for him
   to work through; do not offer to do it.

## What each check means

| Check | Why it matters |
|---|---|
| `journal-week-pattern` | **The expensive one.** The daily template dispatches on `/^\d{1,2}\s+Week$/i`. A folder named `Week 10` matches nothing, so no weekly template is applied and that week's review silently never generates. Not cosmetic - it is missing writing. |
| `journal-pad` | Unpadded numbers sort as text: `10 October` lands before `9 September`, `3 Week` after `28 Week`. This is the whole reason the explorer looks wrong. |
| `journal-lang` | A German month name (`5 Mai`) means Obsidian's display language was German when that folder was created - moment.js follows it. Check Settings → General → Language, or it drifts again. Not readable from disk; it lives in localStorage. |
| `folder-note-missing` | A hub folder with no folder note does not open when clicked. In the journal it also means a missing weekly/monthly/yearly rollup. |
| `no-note-type` | **Read this one carefully.** Bases filter on `note_type`, so a note without it is invisible to every view. The note still exists and still opens; it just cannot be found any way except search. |
| `no-frontmatter` | Often fine. Much of the older material predates the convention, and CLAUDE.md forbids inventing a `created` date for a note that has none. Worth adding `note_type` only where a Base should be picking the note up. |
| `frontmatter-unclosed` / `frontmatter-malformed` | **Fix immediately.** The note has no valid properties at all and has vanished from every Base. This is the failure a `perl -pe` pattern ending in `\s*$` caused here before. |
| `base-dead-newitemfolder` | Fails quietly: the view still renders, but "new note from this base" lands in the wrong place or fails. |
| `base-dead-path` | A base filter naming a folder that no longer exists renders an empty view, with no error. |
| `orphan` | A note with no inbound links. A smell, not a defect - say so rather than leaving it silently unlinked. |

## Use it as a restructure gate

`base-dead-newitemfolder` and `base-dead-path` are the two checks that catch a folder
rename breaking things, because Obsidian does not update Base filters when a folder
moves and never will.

Run `tidy.py` **before** a restructure and record the counts. Run it **after**. Any
increase in a `base-dead-*` count is a path the rename broke, and it is the only
warning you get - nothing errors, the view just empties.

## What it deliberately does not check

Whether a note is any *good*. This is structure only. For "where am I actually
struggling", read the journal - that is `consult`, not this.

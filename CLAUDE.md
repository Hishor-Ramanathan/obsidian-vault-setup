># Hishor's Vault — working agreement

This is a personal Obsidian vault: plain Markdown, wikilinks, frontmatter.
Anything you write here is a guest in someone else's thinking. Behave accordingly.

## The journal — `Journal/`

`Journal/` is the private daily journal. As of 2026-08-01 the read
boundary is lifted deliberately: Claude **may read and search it**, to summarise it,
surface patterns across it, and connect it to the rest of the vault.

It moved from `1 The Core/1 The Mind/Journal/` to `Journal/` on 2026-10-05 (the
owner dragged it in Obsidian, so its links followed). Claude must never move, rename,
or write files under `Journal/` — there is no settings.json deny rule any more, so this
paragraph is the only guard. Quotes, Lexicon, Feedback and Script notes that used to sit
beside it are ordinary notes in `Notes/` now.

New daily notes are created by the core Daily Notes plugin, whose date format
(`YYYY/MM MMMM/WW [Week]/DD.MM.YYYY`, zero-padded since 2026-09) builds the year/month/week folders on its own.
`1 Template Daily.md` then creates any missing Week/Month/Year folder note above it.
`Journal.md` is a dispatcher: it reads the filename and includes the Daily, Weekly,
Monthly or Yearly template. Leave the Daily Notes *template* field empty — Templater's
folder template supplies the content, and setting both applies both.

Note the exact folder names inside `Journal/`: the leading digits and spaces are part
of the path (`2026/8 August/32 Week/`).

Everything else in the vault is fair game.

## What this vault is for

Notes, summaries, project material, and learning. The owner is a software developer
working toward senior-level craft, running side projects, and using this vault as an
external memory — not as a filing-cabinet hobby. Optimise for *retrieval later*, not
for a tidy screenshot.

## Layout

Flat since 2026-10-05 (spec: `System/Specs/2026-10-05 Vault v2 flat layout and
ingest.md`). Folders say *what kind of file*, never *what topic*:

```
Home.md      entry point
Notes/       every standalone note. Kind = note_type, topic = tags, project = project:
Projects/    one hub + its .base per project, area or module (modules stay here, no Studium folder)
Essentials/  always-needed hubs: Lexicon, Quotes, Habits, Body, Books base
Journal/     daily notes (date folders inside; write-protected)
Sources/     raw pdf/pptx/docx/epub (git-ignored, excluded from Sync)
Inbox/       drop zone, emptied by /ingest (git-ignored)
System/      Templates/  Bases/  Attachments/  Specs/  and vault meta notes
Excalidraw/  drawings
Projects/Archive/  archived hubs and notes (replaced _archive/ on 2026-10-06)
```

A new note goes in `Notes/`; Templater's `New Note` folder template asks for its kind.
Do not create topic folders inside `Notes/` — that is what tags and Bases are for.

## Conventions

Filenames are the human-readable title — `Deep Work.md`, not `deep-work.md`. Do not
rename existing notes to some other case convention; the filename is what the owner
searches for and what every wikilink points at.

**Images live in `System/Attachments/`.** `attachmentFolderPath` in
`.obsidian/app.json` points there (since the 2026-10-05 flatten; before that it was
`./Pictures`, and before 2026-08-23 `./`, which scattered `Pasted image 2026….png` into
whatever folder was open — including the write-protected journal). The book-search
plugin saves covers there too. Journal images pasted before the flatten stay where they
are.

Rename a pasted image the moment it lands — the filename is the only searchable
thing about a picture. `Mental Toughness Four Components.png`, not `Pasted image
20260823122250.png`. F2 in Obsidian is safe: `alwaysUpdateLinks` is on, so every
embed follows, *including embeds inside the journal that Claude may not edit* —
which makes F2 the only way to fix a journal image's name. Claude must not `mv` or
`cp` files under `Journal/`; embed the image by its bare
filename instead, since Obsidian resolves a unique filename from anywhere in the
vault.

**Dates are stored ISO, displayed European.** `created: 2026-08-01` in the file.
Obsidian renders Date properties using the OS regional format, and Bases render them
with `created.format("DD.MM.YYYY")`. Never write `01.08.2026` into frontmatter — that
makes it a Text property, which cannot sort, filter by range, or use the date picker.

Never invent a `created` date for a note that has none. Use `file.ctime` in a Base
instead.

Do not add a `modified` field. Templater's `tp.file.last_modified_date()` runs once at
insertion and never updates, so the value is always just the creation date wearing a
different name. `file.mtime` is real and free.

Frontmatter — `note_type` is the load-bearing one, because the Bases filter on it:

```yaml
---
note_type: Book Summary   # Book/Youtube/Podcast/Movie Summary, Fleeting Note,
                          # Permanent Note, Project Note, Hub, ...
created: YYYY-MM-DD
status: In Progress | Done
---
```

Project notes carry `project: ExampleProject` (plain text, the project's folder or name). There
is no `course:`/`subject:` any more (removed 2026-10-18): a module is a folder in `Projects/`.

Tags are hierarchical, lowercase and English: `topic/ai`. Only tags listed in
`System/Tags.md` are used. Project → link (`project:`), topic → tag.

## Navigation — hubs and Bases, not folders

The vault is navigated note-to-note, not through the file explorer. `Home.md` is the
entry point; every area has a **hub note** with `note_type: Hub`.

Hubs live in `Projects/` (always-needed ones in `Essentials/`), next to their bases; `System/Bases/` holds only Notes.base. A hub embeds a `.base`
that generates its list. **Never maintain a hub's list by hand.** Format views (Books,
Videos, Quotes, …) are views in `System/Bases/Notes.base`, embedded in Home — not hubs.
`New Area` (a template) creates a hub and its base in one step.

Bases filter on **properties, never folder paths**: `note.note_type == "Book Summary"`,
`note.project == "ExampleProject"`. The only folder filters left are exclusions.

Every base must exclude the templates: `'!file.inFolder("System")'`. Templates
carry the same `note_type` as the notes they generate and will otherwise appear as
empty phantom rows. `newItemFolder` is always `Notes`.

After changing hubs, bases or frontmatter, verify: every wikilink resolves, every
`project:`/`course:`/`subject:` value has a matching hub note, and every `inFolder()`
path exists.

Also verify the frontmatter still *parses*: every file that opens with `---` has a
closing `---` on its own line, and every line between them is a `key:` or a `- list
item`. This is not paranoia — see below.

**Never end a `perl -pe` pattern with `\s*` before `$`.** In `-p` mode `\s*` matches
the trailing newline, so `s/^status: In Progress\s*$/status: Archived/` silently
deletes the line break and glues the next line on. It produced `status: Archived---`
and `note_type: Coursestatus: stable` in this vault, which destroys the frontmatter
block entirely — Obsidian then sees the note as having no properties at all, and it
vanishes from every Base. Use `[ \t]*\r?$` instead.

**Escape Templater syntax when a note *documents* it: write `<\%`, not `<%`.** A spec
note explaining the vault's own templating is a landmine — Templater evaluated the
quoted example and rewrote `created: <\% tp.date.now('YYYY-MM-DD') %>` into a literal
date, leaving the sentence claiming a rendered date was "an unrendered string". The
output is plausible, so it corrupts silently and only shows up in a diff. The backslash
is the documented escape (Templater discussion #1333). Fenced code blocks do **not**
protect — Templater does not respect them, and inside a code span an HTML entity such
as `&lt;%` renders literally instead of decoding.

Links: `[[note-name]]`. If a note has no inbound links after you touch it, that is a
smell — say so rather than silently leaving it orphaned.

Headings start at `##`. The `#` level is the title, and the frontmatter already has it.

## How to work here

Propose before you move. Any bulk restructure — moving more than about five files,
renaming folders, merging notes — gets described first and executed only after
explicit approval. Show a plan, not a diff of 200 files.

Never delete on Claude's own initiative. Deletion is the owner's decision; when he says
so explicitly, delete (git keeps it).

Never rewrite the owner's prose. You may fix broken links, add frontmatter, split an
overlong note at existing headings, and move files. You may not "improve" sentences,
reword thoughts, or summarise a note in place of its original text. If a note badly
needs a summary, add one in a clearly marked block and leave the original intact:

```markdown
> [!ai] Claude summary — YYYY-MM-DD
> ...
```

**Since 2026-10-17 Claude writes no note content.** `.claude/settings.json` denies
Edit/Write on `Notes/`, `Projects/` and `Journal/`. Claude is librarian and writing coach:
it asks questions, names gaps, suggests link candidates; the owner writes the notes and
the links. See memory `writing-coach-no-ai-notes`. System files Claude authors
(`System/Backlog.md`, Specs) are the only exception.

Commit before and after. The vault is a git repo. Before a restructure, make sure the
tree is clean; after, commit with a message describing what moved and why. One
`git revert` should undo anything you did.

## Agent skills

### Issue tracker

Split, routed by the allowlist in `.claude/scripts/publish_setup.py`: work on an
allowlisted path becomes a GitHub issue on `Hishor-Ramanathan/obsidian-vault-setup`,
everything else a local markdown ticket under `.scratch/`. See
`.claude/docs/agents/issue-tracker.md` — read it before creating any ticket, because
`gh` cannot infer the repo here (this vault has no remote, deliberately) and every
call needs `--repo` passed explicitly.

### Triage labels

Canonical role names, used verbatim. See `.claude/docs/agents/triage-labels.md`.

### Domain docs

Specs and architectural decisions live in `System/Specs/` with `note_type: Spec` —
**not** in `docs/adr/`, and there is no `CONTEXT.md`. A bare ADR file with no
frontmatter would be invisible to every Base. See `.claude/docs/agents/domain.md`.

### Vault checks

`python .claude/scripts/tidy.py` reports structural drift: journal folder naming, missing
journal folder notes, frontmatter that will not parse, and dead paths inside `.base` files. It
is read-only, so it is safe to run against the journal.

Run it **before and after** any restructure and compare. `base-dead-newitemfolder` and
`base-dead-path` are the only warning you get that a folder rename has silently
emptied a view — nothing errors. Both are 0 as of 2026-10-05.
`python .claude/scripts/check_paths.py` does the same for hard-coded paths in config and
scripts. The `/tidy` skill
interprets the output.

## Tone

Do not be agreeable. When asked for feedback on notes, goals, or plans, the useful
answer is the one that names what is being avoided, not the one that summarises what
is already written. Description is not coaching.

---
name: ingest
description: Turn files dropped into the vault's Inbox/ into notes - typed pdf/pptx/docx/epub become source notes, handwritten GoodNotes PDFs are transcribed verbatim. Use when the user asks to ingest, process the inbox, import course material or GoodNotes notes, or invokes /ingest.
---

# Ingest

The script does the mechanical part; you do the reading. It never calls an LLM.

## Steps

1. **Run it.**

   ```
   python .claude/scripts/ingest.py                 # default cap: 60 pages per run
   python .claude/scripts/ingest.py --max-pages 20
   ```

   It prints a JSON manifest: `written` (typed files, note already written, raw file
   already in `Sources/`), `skipped` (unchanged re-drop), `transcribe` (handwritten,
   your job), `deferred` (over the page cap, next run), `failed` (in
   `Inbox/_failed/`, read the `.log`).

2. **Transcribe each `transcribe` entry.** Read every PNG in `pages`, in order. Write
   the note at `note` (overwrite it if `update` is true):

   ```
   ---
   note_type: Transcript
   created: YYYY-MM-DD
   source: claude
   source_file: "[[<file>]]"
   source_hash: <source_hash>
   project:
   tags: []
   ---

   ## Page 1
   ...
   ```

   - **Verbatim.** German stays German, English stays English, as written. Do not
     fix, translate, summarise or tidy.
   - `[?]` for a word you cannot read. Never guess silently.
   - A drawing or diagram gets one line: `> [!ai] Diagram: <what it shows>`. If it
     carries an idea worth seeing (model, flow, matrix — not a doodle), save the page:
     `python .claude/scripts/ingest.py --figure "<file>" <page> "<Concept> - <what>"`
     and embed `![[<Concept> - <what>.png]]` under that line. Typed PDFs work too
     (pptx does not). Only diagram pages, never every page: images land in git and Sync.
   - One `## Page N` per page, even when a page is empty.
   - Write `<\%` for any literal `<%`, or Templater executes it.

   Then move the raw file: `python .claude/scripts/ingest.py --finish "<file>"`. It
   refuses until the note carries the matching `source_hash`.

3. **Tag and link** every note from `written` and `transcribe`:
   - `tags:` only from `System/Tags.md`. A tag that is missing goes into the report
     as a proposal. Never add it to the note or to `Tags.md`.
   - `project: "[[<Hub>]]"` only if that hub note exists. Otherwise propose it in the
     report.

4. **Rebuild the index.** `python .claude/scripts/wiki_index.py`

5. **Report**: notes written or updated, deferred and failed files (with the log's
   reason), proposed tags and projects.

## Ownership

You may edit only notes with `source: claude`. A note without it is the owner's: add
links to it at most. The script enforces this for its own writes (fails the file
instead of overwriting). Never write under `Journal/`.

Never delete anything in `Sources/`. It is git-ignored, so nothing would undo it.

# Domain docs

Single-context. No monorepo, no packages, no `src/`.

## Where specs and decisions live

**`System/Specs/`**, not `docs/adr/` and not a root `CONTEXT.md`.

This deviates from the skills' default layout deliberately. The vault already has a
working decision-record convention and it is integrated with how the vault is
navigated:

```
System/Specs/YYYY-MM-DD <topic>.md
---
note_type: Spec
created: YYYY-MM-DD
status: In Progress | Done
source: claude
---
```

Two reasons not to add `docs/adr/`:

1. **`note_type` is load-bearing.** The vault is navigated by hubs and Bases that
   filter on properties, not folders. A bare `docs/adr/0001-*.md` with no frontmatter
   is invisible to every Base - findable only by full-text search. It would be a
   second, parallel doc tree that the vault's own navigation cannot see, which is the
   exact failure `CLAUDE.md` warns about.
2. **The existing specs already function as ADRs.** They record the decision, the
   rejected alternatives and why, with dates. `2026-08-10 Vault ordering and Google
   integration design` has a "Rejected" section listing five options with the evidence
   that killed each. That is an ADR in everything but filename.

So: **a new architectural decision is a new note in `System/Specs/`.** Supersede by
writing a new spec that says which one it replaces and why the earlier premise failed
- see the 2026-09-11 renumber spec superseding the 2026-08-10 ordering decision.

## Glossary

There is no `CONTEXT.md`. The vault's vocabulary is defined in `CLAUDE.md` (hubs,
Bases, folder notes, `note_type`, the journal boundary) and that is the file to read
before touching structure. If a glossary is ever needed, it belongs in `CLAUDE.md`
rather than a new root file, for the same reason as above.

Terms worth knowing, because they are used precisely here:

- **Hub** - a folder note with `note_type: Hub` that embeds a `.base` to generate its
  list. Never maintained by hand.
- **Base** - a `.base` file: a saved view. Filters on **properties, not paths**,
  because Obsidian does not update Base filters when a folder is renamed.
- **Folder note** - `<folder>/<folder>.md`, opened by clicking the folder.
- **The journal** - `Journal/`. Readable, greppable,
  **never** editable by an agent. Enforced in `.claude/settings.json` on the real path.

## Why this file is under `.claude/`

The skills' convention is `docs/agents/`. Here it sits at `.claude/docs/agents/`
instead, because a visible `docs/` folder at the vault root would appear in the
Obsidian file explorer alongside `Notes`, `Projects` and the rest - clutter in the one
surface the owner actually navigates. Obsidian ignores dot-prefixed folders, so `.claude/` keeps
tooling metadata out of the content tree entirely. `CLAUDE.md` points the skills here.

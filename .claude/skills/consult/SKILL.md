---
name: consult
description: Retrieve the lessons from the vault's book summaries that fit the owner's current state. Use when the user asks what to read, what a book says about their situation, "what do my books say about this", "consult my vault", or invokes /consult. Reads the journal for current state, then matches against book summaries that actually have content.
---

# Consult

Match the vault's own material against where the owner is *now*. Retrieval, not organisation.

## Steps

1. **Read the current state.** The last 10-14 daily entries in
   `Journal/<year>/<month>/<week>/DD.MM.YYYY.md`.
   Read-only — never edit the journal. Note what is actually happening: the
   live problem, the mood, what got dropped. Entries are English/German mixed.

2. **Find the books with content.** `wc -w` over the notes in `Notes/` with
   `note_type: Book Summary` (`grep -l "^note_type: Book Summary" Notes/*.md`).
   **Under ~100 words means empty template shell — skip it.** Only read the
   ones with real content.

3. **Read the 3-4 whose subject matter plausibly touches the current state.**
   Do not skim titles and guess. Open them.

4. **Return at most 3 lessons.** Each one:
   - the quote, verbatim from the summary, with the book and the note link
   - **who wrote that summary** — see the provenance rule below
   - the journal entry it answers, with the date
   - what it means for the decision in front of him this week

## Not every summary is his

Some book summaries were written by other members of the club and copied in from
`OtherVault`. They carry frontmatter saying so:

```yaml
summary author: "[[Pavidiran Ramanathan]]"   # or: unknown
origin: OtherVault
```

**Check that field before quoting, every time.** If `summary author` names someone
other than him, or `origin: OtherVault` is present, say whose words they are:

> *"Pavidiran's summary of [[How to Win Friends and Influence People]] says …"*

Never present another member's reading as his own. The premise of this skill is that
*his* vault answers *him*; a quote silently attributed to him that he never wrote
breaks that, and he would have no way to tell.

It is still worth surfacing — knowing a club member has already read the book he
needs is useful in itself, and is a reason to go and ask them. Say that instead of
suppressing it.

## Rules

- Quote the summaries in the vault, never the book from your own memory. If the note
  doesn't say it, it doesn't count — the whole point is that the vault answers him.
- If the relevant book is an empty shell, say so and name it. That is the finding,
  not a failure. Before calling one empty, check whether a fuller version exists in
  `<other-vault>` — two shells here were filled from there on
  2026-09-12, and others may still be worth pulling.
- Three lessons maximum. A list of ten is a reading list, and a reading list is
  how he avoids the one thing.
- Do not append the output to a note unless asked.

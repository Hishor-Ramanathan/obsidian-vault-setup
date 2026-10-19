# Issue tracker: split, routed by the publish allowlist

This vault tracks work in **two places**, because some of it can be public and some of
it can never be. The routing rule is not a fresh judgement call: it reuses the
allowlist that `.claude/scripts/publish_setup.py` already enforces, so "can this be
tracked in public" has the same answer as "can this be published" - one boundary,
asserted in one place.

## The rule

**Does the work touch a path in `publish_setup.py`'s `ALLOW` list?**

| | Yes | No |
|---|---|---|
| Where | GitHub issue on `Hishor-Ramanathan/obsidian-vault-setup` | Local markdown under `.scratch/` |
| Covers | templates, `.claude/skills`, `.claude/scripts`, `.base` files, `.obsidian/*.json`, `CLAUDE.md`, `Home.md` | notes, specs, journal, Sessions, People, Feedback, anything under `DENY` |
| Why there | it is already public, so the issue can be too, and outside feedback is the point | the issue would have to quote or name private material to be useful |

**One refinement.** An issue about a *pattern* that happens to affect private notes goes
to **GitHub, described generically** - never local just because a private file
triggered it. Issue #4 is the worked example: it describes notes without `note_type`
being invisible to every Base, without naming the personal note that revealed it.
Generalising costs one sentence and keeps the finding where people can answer it.

When genuinely unsure, local. A ticket in the wrong place is an inconvenience; a
private note title on a public repo is not retractable.

## GitHub half

Use the `gh` CLI. **Always pass `--repo` explicitly:**

```
gh issue create --repo Hishor-Ramanathan/obsidian-vault-setup --title "..." --body "..."
gh issue list   --repo Hishor-Ramanathan/obsidian-vault-setup --state open
gh issue view   --repo Hishor-Ramanathan/obsidian-vault-setup <n> --comments
gh issue edit   --repo Hishor-Ramanathan/obsidian-vault-setup <n> --add-label "..."
gh issue close  --repo Hishor-Ramanathan/obsidian-vault-setup <n> --comment "..."
```

`gh` normally infers the repo from `git remote -v`. **That does not work here.** This
vault has no remote on purpose - Obsidian Sync is the backup, and git is local only so
that one `git revert` can undo a restructure. Omit `--repo` and `gh` fails with a
confusing error about not being in a repository.

Use a heredoc for multi-line bodies.

### Closing issues from the publish commit

The public repo is **generated**, not hand-edited. So the loop is:

1. Fix it in the vault.
2. `python .claude/scripts/publish_setup.py <staging-dir>`
3. Commit in the staging clone with a closing keyword: `Closes #2`.
4. Push. GitHub closes the issue on merge to the default branch.

That is what makes tracking cheap: the act of publishing a fix is the act of closing
its ticket. Never close an issue by hand that a publish is about to close.

## Local half

One file per ticket under `.scratch/<slug>/issues/<NN>-<name>.md`, numbered from `01`
in dependency order, blockers first. Each file carries a `**Blocked by:**` line naming
the tickets that gate it, and a `**Status:**` line using the same role strings as the
GitHub labels (see `triage-labels.md`), so one vocabulary covers both halves.

`.scratch/` is gitignored. It is working state, not vault content, and it must never
be picked up by a Base - it carries no `note_type` and lives outside the numbered
content tree.

## Pull requests as a request surface

**No.** The vault has no remote and no contributors; the setup repo takes issues, not
feature PRs. `/triage` reads this flag.

## When a skill says...

- *"publish to the issue tracker"* - apply the rule above, then create a GitHub issue
  or write a `.scratch/` file.
- *"fetch the relevant ticket"* - `gh issue view --repo … <n> --comments`, or read the
  `.scratch/` file.
- *"apply the ready-for-agent label"* - on GitHub, `gh issue edit --add-label`; locally,
  set the `**Status:**` line.

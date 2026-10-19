# Triage labels

The `triage` skill works in canonical role names and needs a mapping to the strings
this project actually uses. Here they are identical - the canonical names are used
verbatim, so there is nothing to translate.

## Category roles - exactly one per triaged issue

| Canonical | Label | Already existed |
|---|---|---|
| `bug` | `bug` | yes, GitHub default |
| `enhancement` | `enhancement` | yes, GitHub default |

## State roles - exactly one per triaged issue

| Canonical | Label | Already existed |
|---|---|---|
| `needs-triage` | `needs-triage` | created 2026-09-11 |
| `needs-info` | `needs-info` | created 2026-09-11 |
| `ready-for-agent` | `ready-for-agent` | created 2026-09-11 |
| `ready-for-human` | `ready-for-human` | created 2026-09-11 |
| `wontfix` | `wontfix` | yes, GitHub default |

An unlabelled issue goes to `needs-triage` first. From there: `needs-info`,
`ready-for-agent`, `ready-for-human` or `wontfix`. `needs-info` returns to
`needs-triage` once the reporter replies.

## Both halves of the split tracker, one vocabulary

On GitHub these are labels:

```
gh issue edit --repo Hishor-Ramanathan/obsidian-vault-setup <n> --add-label ready-for-agent
```

Under `.scratch/` they are the `**Status:**` line in the ticket file. Same strings, so
a ticket keeps its meaning if it ever moves between the two halves. See
`issue-tracker.md` for which half a given piece of work belongs in.

## Unused GitHub defaults

`documentation`, `duplicate`, `good first issue`, `help wanted`, `invalid` and
`accessibility` came with the repo and are not part of the role vocabulary. They are
harmless; `triage` ignores anything that is not a category or state role. Leave them
rather than deleting, in case an outside contributor reaches for one.

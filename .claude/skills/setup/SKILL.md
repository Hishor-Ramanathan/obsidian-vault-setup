---
name: setup
description: Set up this vault on a new machine or fresh clone - install the community plugins, seed the folder settings, verify structure. Use when the user asks to set up the vault, restore plugins, bootstrap a new computer, or invokes /setup.
---

# Setup

Take a fresh clone of the public setup repo to a working vault. The repo carries
structure, templates, bases, skills and config JSONs. It does **not** carry notes,
plugin code, or secrets, so this skill supplies those steps.

**Run in order. Stop and report if a step fails.**

## Steps

1. **Check the folder.** `.obsidian/community-plugins.json` and `System/Templates/`
   must exist. If not, this is not the setup repo: stop.

2. **Install plugins and seed settings.**

   ```
   python .claude/scripts/install_plugins.py
   ```

   It installs every id in `community-plugins.json` from its latest GitHub release and
   writes each plugin's published settings (`.claude/seeds/<id>.json`: icons, Templater
   folders, Dataview, Excalidraw, Terminal, ...) when it has no `data.json`. Accounts,
   tokens and private paths are never in the seeds.
   Re-running is safe: installed plugins are skipped.

3. **Tab Groups: use the fork build** until upstream PR
   `imsang27/obsidian-tab-groups#44` (setting *Lock grouped tabs*) is merged. Check
   `gh pr view 44 --repo imsang27/obsidian-tab-groups --json state`. If still open:

   ```
   git clone -b feat/lock-grouped-tabs https://github.com/Hishor-Ramanathan/obsidian-tab-groups <empty-dir>
   cd <empty-dir> && npm ci && npm run build
   ```

   Copy `main.js` over `.obsidian/plugins/tab-groups/main.js`. If merged, step 2 already
   installed a release that has the setting once the maintainer cuts one.

4. **Tell the owner what only he can do**, then stop. Do not attempt these:
   - Open the folder as a vault in Obsidian, trust the plugins, enable them.
   - Theme: shipped in `.obsidian/themes/`. Settings -> Appearance should already show
     **AnuPpuccin** selected with the CSS snippets enabled.
   - Secrets: Full Calendar's Google sign-in, any API keys for Claudian. They live in
     each plugin's `data.json` and are never committed.
   - Obsidian Sync, if wanted.

5. **Verify.**

   ```
   python .claude/scripts/tidy.py
   python .claude/scripts/check_paths.py
   ```

   `check_paths.py` must report 0 dead. Journal findings on an empty vault are expected.

## Rules

- Never write secrets, tokens or OAuth values anywhere.
- Never create topic folders in `Notes/`; the layout is in `CLAUDE.md`.
- Plugin `data.json` beyond the seeded keys is the owner's, not the repo's.

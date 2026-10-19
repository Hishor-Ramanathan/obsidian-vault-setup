"""Read Google Tasks using the credentials Full Calendar Remastered already stored.

    python .claude/scripts/tasks.py            # open tasks
    python .claude/scripts/tasks.py --all      # + completed
    python .claude/scripts/tasks.py --md       # markdown checkboxes, ready to paste

No cache on purpose: the API call is ~1s, and a stale cache is worse than a slow
one. Add caching only if the round-trip ever actually gets in the way.
"""

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

TIMEOUT = 20  # seconds; without it a stalled connection hangs /brief forever
CONFIG = Path(__file__).resolve().parents[2] / ".obsidian/plugins/full-calendar-remastered/data.json"


def access_token(config):
    """Trade the plugin's stored refresh token for a short-lived access token."""
    account = config["googleAccounts"][0]
    if not account["refreshToken"]:
        sys.exit(RECONNECT % "no refresh token stored")
    body = urllib.parse.urlencode({
        "client_id": config["googleClientId"],
        "client_secret": config["googleClientSecret"],
        "refresh_token": account["refreshToken"],
        "grant_type": "refresh_token",
    }).encode()
    try:
        return json.load(urllib.request.urlopen("https://oauth2.googleapis.com/token", body, timeout=TIMEOUT))["access_token"]
    except urllib.error.HTTPError as e:
        # invalid_grant = token expired or revoked. A "Testing" OAuth app gets 7-day tokens.
        sys.exit(RECONNECT % e.read().decode())


RECONNECT = ("Google refused the Full Calendar login (%s).\n"
             "Fix: Obsidian -> Settings -> Full Calendar -> Google account -> reconnect.")


def get(url, token):
    return json.load(urllib.request.urlopen(
        urllib.request.Request(url, headers={"Authorization": "Bearer " + token}), timeout=TIMEOUT))


def main():
    show_all = "--all" in sys.argv
    as_markdown = "--md" in sys.argv

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    token = access_token(config)

    total = 0
    for task_list in get("https://tasks.googleapis.com/tasks/v1/users/@me/lists", token).get("items", []):
        url = ("https://tasks.googleapis.com/tasks/v1/lists/%s/tasks"
               "?showCompleted=%s&showHidden=%s&maxResults=100"
               % (task_list["id"], str(show_all).lower(), str(show_all).lower()))
        tasks = get(url, token).get("items", [])
        if not show_all:
            tasks = [t for t in tasks if t.get("status") != "completed"]
        total += len(tasks)

        if not tasks and not as_markdown:
            print("=== %s  (leer)" % task_list["title"])
            continue
        if not tasks:
            continue

        print("=== %s" % task_list["title"])
        for task in tasks:
            done = "x" if task.get("status") == "completed" else " "
            due = task.get("due", "")[:10]
            suffix = "  (due %s)" % due if due else ""
            print("- [%s] %s%s" % (done, task.get("title", "").strip(), suffix))

    print("\n%d Task(s)." % total)


if __name__ == "__main__":
    main()

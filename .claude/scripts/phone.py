"""Read the phone's daily numbers off a dedicated Google Calendar.

    python .claude/scripts/phone.py             # last 14 days
    python .claude/scripts/phone.py --days 30
    python .claude/scripts/phone.py --selftest

The phone pushes; Windows reads. Nothing here talks to the phone, because nothing
can: Health Connect "is a database that's stored on your device… Google doesn't use
the cloud to store data" (https://support.google.com/android/answer/13770320), and
Digital Wellbeing has no export at all. Google Fit's REST API is shut to new
developers and ends in 2026, so it is not an option either
(https://developer.android.com/health-and-fitness/health-connect/migration/fit/faq).

So: a nightly Tasker task writes one all-day event per day onto a calendar kept
separate from the real ones, and this reads it back. Calendar rather than a file in
the vault because Obsidian on Android gives no documented guarantee that it will
re-index a file written by another app.

Event shape - the description is `key=value` lines, so adding a metric later needs
no change here:

    title:        2026-09-12
    description:  screen=8h12m
                  unlocks=142
                  sleep=6h05m
                  exercise=45m
                  mindfulness=10m
"""

import re
import sys
import urllib.parse
from datetime import date, timedelta

from tasks import CONFIG, access_token, get   # same OAuth rail as Google Tasks

CALENDAR_NAME = "Signals"
DURATION = re.compile(r"(?:(?P<hours>\d+)h)?\s*(?:(?P<mins>\d+)m)?$")


def parse_duration(value):
    """'8h12m' -> 492 minutes. Returns None for anything that is not a duration."""
    match = DURATION.fullmatch(value.strip())
    if not match or not any(match.groupdict().values()):
        return None
    return int(match["hours"] or 0) * 60 + int(match["mins"] or 0)


def parse_description(text):
    """`key=value` lines into a dict, durations converted to minutes."""
    readings = {}
    for line in (text or "").splitlines():
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        minutes = parse_duration(value)
        readings[key.strip()] = minutes if minutes is not None else value.strip()
    return readings


def calendar_id(token, name=CALENDAR_NAME):
    listing = get("https://www.googleapis.com/calendar/v3/users/me/calendarList", token)
    for entry in listing.get("items", []):
        if entry.get("summary") == name:
            return entry["id"]
    return None


def readings(days=14, token=None):
    """date -> {metric: value}, newest last. Empty if the calendar does not exist."""
    token = token or access_token(json_config())
    board = calendar_id(token)
    if board is None:
        return {}

    start = date.today() - timedelta(days=days)
    query = urllib.parse.urlencode({
        "timeMin": start.isoformat() + "T00:00:00Z",
        "singleEvents": "true",
        "maxResults": 250,
        "timeZone": "Europe/Zurich",   # the FHNW and Familie calendars are UTC; always pin this
    })
    url = ("https://www.googleapis.com/calendar/v3/calendars/%s/events?%s"
           % (urllib.parse.quote(board), query))

    found = {}
    for event in get(url, token).get("items", []):
        stamp = (event.get("start", {}).get("date")
                 or event.get("start", {}).get("dateTime", "")[:10])
        if not stamp:
            continue
        found[date.fromisoformat(stamp)] = parse_description(event.get("description"))
    return dict(sorted(found.items()))


def json_config():
    import json
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def selftest():
    assert parse_duration("8h12m") == 492
    assert parse_duration("45m") == 45
    assert parse_duration("6h") == 360
    assert parse_duration("142") is None, "a bare count is not a duration"
    assert parse_duration("nonsense") is None
    parsed = parse_description("screen=8h12m\nunlocks=142\njunk line\nnote=long day")
    assert parsed == {"screen": 492, "unlocks": "142", "note": "long day"}, parsed
    print("selftest ok")


def main():
    if "--selftest" in sys.argv:
        return selftest()

    days = 14
    if "--days" in sys.argv:
        days = int(sys.argv[sys.argv.index("--days") + 1])

    found = readings(days)
    if not found:
        print("No '%s' calendar, or no events in %d days.\n"
              "Create a secondary calendar called '%s' in Google Calendar, then point\n"
              "the nightly Tasker task at it." % (CALENDAR_NAME, days, CALENDAR_NAME))
        return 0
    for day, metrics in found.items():
        print(day, " ".join("%s=%s" % pair for pair in sorted(metrics.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())

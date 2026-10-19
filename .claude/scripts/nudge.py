"""Notice one thing worth asking about, and push it to the phone.

    set NTFY_TOPIC=<your-secret-topic>
    python .claude/scripts/nudge.py            # send the strongest signal
    python .claude/scripts/nudge.py --all      # print every signal, send nothing
    python .claude/scripts/nudge.py --dry-run
    python .claude/scripts/nudge.py --selftest

The vault waits to be opened, which is the whole problem: it cannot ask about a day
it never saw. This inverts that - a scheduled run looks for something odd and opens
the conversation itself.

Why ntfy and not an Obsidian plugin: on Android "Obsidian can't run plugin code in
the background", so no reminder plugin fires unless the app is already open
(https://uphy.github.io/obsidian-reminder/guide/notification.html). Every mobile
option routes through an external push service anyway.

PRIVACY: an ntfy.sh topic is a public URL to anyone who guesses the name. Use a long
random one - `python -c "import secrets;print(secrets.token_urlsafe(16))"` - or point
NTFY_SERVER at your own instance.
"""

import os
import re
import sys
import urllib.request
from collections import namedtuple
from statistics import median
from datetime import date

import phone
from habits import DAILY_NAME, JOURNAL, read_ledger, score

SERVER = os.environ.get("NTFY_SERVER", "https://ntfy.sh")
NEAR, FAR = 14, 90
QUIET_DAYS = 3          # writing nothing for this long is itself worth asking about
PHONE_FLOOR = 240       # minutes; below this a spike is not worth a notification
PHONE_SPIKE = 1.5       # times the median before it counts as unusual
PHONE_MIN_DAYS = 5      # no median worth trusting below this
# Everything between the `# Note` heading and the next heading.
NOTE_SECTION = re.compile(r"^#+ Note[ 	]*$(?P<text>.*?)(?=^#|\Z)",
                          re.M | re.S)

# Higher urgency wins. A silent vault outranks a habit gap, because when the vault is
# silent the habit data is missing rather than bad, and asking about it would be noise.
Signal = namedtuple("Signal", "urgency title body")


def last_journalled(journal=JOURNAL):
    """The most recent day whose daily note has anything written under `# Note`.

    File mtime is not usable here: bulk-copied notes and Obsidian Sync both touch it,
    so the vault can look busy on a day nothing was written. The `# Note` body is the
    one place only the owner types.
    """
    written = None
    for note in journal.rglob("*.md"):
        stamp = DAILY_NAME.match(note.stem)
        if not stamp:
            continue
        body = NOTE_SECTION.search(note.read_text(encoding="utf-8", errors="replace"))
        if not body or not body.group("text").strip():
            continue
        day, month, year = (int(part) for part in stamp.groups())
        entry = date(year, month, day)
        written = entry if written is None else max(written, entry)
    return written


def silence_signal(today=None):
    written = last_journalled()
    if written is None:
        return None
    quiet = ((today or date.today()) - written).days
    if quiet < QUIET_DAYS:
        return None
    return Signal(
        urgency=2,
        title="%d days unwritten" % quiet,
        body="Nothing written in the journal since %s. What happened this week "
             "that is worth keeping?" % written.strftime("%A %d %B"),
    )


def phone_signal(days=14):
    """An unusual day on the phone, phrased as a question about that day.

    Compared against this owner's own median rather than a fixed threshold: a fixed
    one either fires every day or never, and "a lot of screen time" only means
    anything relative to a normal week.
    """
    try:
        history = phone.readings(days)
    except Exception:
        return None          # scheduled job: no network is not a reason to go silent

    screen = {day: metrics["screen"] for day, metrics in history.items()
              if isinstance(metrics.get("screen"), int)}
    if len(screen) < PHONE_MIN_DAYS:
        return None

    typical = median(screen.values())
    day, minutes = max(screen.items())
    if minutes < PHONE_FLOOR or minutes < typical * PHONE_SPIKE:
        return None

    return Signal(3, "%dh%02dm on your phone" % divmod(minutes, 60),
                  "%s was %.1fx your usual %dh%02dm. What happened?"
                  % (day.strftime("%A"), minutes / typical, *divmod(int(typical), 60)))


def habit_signal(near, far):
    """An unticked box means NO RECORD, never "did not happen".

    The owner does the gym and meditates without ticking anything, so this must ask
    whether the thing happened. Once a passive source feeds the vault, absence becomes
    real evidence and the wording can harden.
    """
    unlogged = [(habit, stats) for habit, stats in near.items()
                if stats["kept"] == 0 and far.get(habit, {}).get("kept", 0) > 0]
    if unlogged:
        habit, stats = unlogged[0]
        return Signal(1, habit, "No record for %d days - last logged %s. Did you do it?"
                      % (stats["offered"], far[habit]["last_kept"]))

    if near and all(stats["kept"] == 0 for stats in near.values()):
        return Signal(1, "Nothing logged",
                      "%d habits, %d days, no ticks. The tracker cannot see anything "
                      "you do away from a desk - is that the whole story?"
                      % (len(near), NEAR))

    worst = next(iter(near), None)
    if worst is None or near[worst]["kept"] == near[worst]["offered"]:
        return None
    return Signal(1, worst, "%d of %d logged in %d days. Streak %d."
                  % (near[worst]["kept"], near[worst]["offered"], NEAR,
                     near[worst]["streak"]))


def collect():
    ledger = read_ledger()
    found = [phone_signal(),
             silence_signal(),
             habit_signal(score(ledger, NEAR), score(ledger, FAR))]
    return sorted((s for s in found if s), key=lambda s: -s.urgency)


def send(signal, topic):
    request = urllib.request.Request(
        "%s/%s" % (SERVER.rstrip("/"), topic),
        data=signal.body.encode("utf-8"),
        headers={"Title": signal.title, "Tags": "thinking_face"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.status


def selftest():
    near = {"Meditate": {"kept": 0, "offered": 5, "streak": 0}}
    far = {"Meditate": {"kept": 3, "offered": 20, "last_kept": "2026-08-10"}}
    assert "Did you do it?" in habit_signal(near, far).body
    assert "stop" not in habit_signal(near, far).body.lower(), "never accuse"
    assert silence_signal(today=date(1970, 1, 1)) is None, "future write is not silence"
    quiet = silence_signal()
    assert quiet is None or quiet.urgency > habit_signal(near, far).urgency
    assert phone_signal(days=0) is None, "no phone data must not raise"

    usual = {date(2026, 9, d): {"screen": 180} for d in range(1, 8)}
    phone.readings = lambda days=14: usual
    assert phone_signal() is None, "a normal week must stay quiet"

    spike = {**usual, date(2026, 9, 8): {"screen": 492}}   # Tuesday, 8h12m
    phone.readings = lambda days=14: spike
    loud = phone_signal()
    assert loud.title == "8h12m on your phone", loud.title
    assert "Tuesday" in loud.body and loud.body.endswith("What happened?"), loud.body
    assert loud.urgency > habit_signal(near, far).urgency, "an anomaly outranks a reminder"
    print("selftest ok")


def main():
    if "--selftest" in sys.argv:
        return selftest()

    found = collect()
    if "--all" in sys.argv:
        for signal in found:
            print("[%d] %s\n    %s" % (signal.urgency, signal.title, signal.body))
        return 0
    if not found:
        print("nothing worth asking about")
        return 0

    signal = found[0]
    if "--dry-run" in sys.argv:
        print("%s\n%s" % (signal.title, signal.body))
        return 0

    topic = os.environ.get("NTFY_TOPIC")
    if not topic:
        print("NTFY_TOPIC is not set - see the docstring", file=sys.stderr)
        return 1
    print("sent (%s): %s - %s" % (send(signal, topic), signal.title, signal.body))
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
Routine learning: notice what the user does at the same time most days and
offer to do it for them.

Everything here stays on the user's computer (in their data folder):

    activity.jsonl   one line per thing they opened or ran
    routines.json    routines they accepted, plus suggestions they declined

How a suggestion is found (suggest_routines):
    - Look at the last LOOKBACK_DAYS *active* days (days LensFlow was used,
      so a weekend away doesn't count against a habit).
    - For each thing they did (open a studio / run an event), take the
      first time they did it each day and its typical time (median).
    - If on at least MIN_DAYS of those days it happened within
      TIME_WINDOW minutes of that typical time, suggest it at that time
      (rounded to 5 minutes). Weekday-only habits become weekday routines.

Nothing runs automatically until the user accepts a suggestion.
"""

import json
import statistics
import time as _time
import uuid
from datetime import datetime, timedelta

from backend.paths import user_config_path


LOOKBACK_DAYS = 7
MIN_DAYS = 4
TIME_WINDOW = 20           # minutes either side of the typical time
DECLINE_SNOOZE_DAYS = 30
KEEP_DAYS = 90             # activity older than this is deleted
RUN_GRACE_MINUTES = 30     # a routine still runs if LensFlow starts this late

WEEKDAYS = [0, 1, 2, 3, 4]
EVERY_DAY = [0, 1, 2, 3, 4, 5, 6]
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


# =========================================================
# ACTIVITY LOG
# =========================================================

class ActivityLog:

    def __init__(self, path=None):
        self.path = path or user_config_path("activity.jsonl")

    def record(self, kind, target, studio=None, trigger="click", when=None, event=None):
        """
        kind: "studio" (opened a studio's page), "launch" (ran all of a
        studio's events) or "event" (ran one event).
        target: studio title or event name. `event` keeps the event itself
        so a routine can run it later.
        """

        when = when or datetime.now()

        entry = {
            "at": when.isoformat(timespec="seconds"),
            "kind": kind,
            "target": target,
            "studio": studio,
            "trigger": trigger,
        }

        if event is not None:
            entry["event"] = event

        try:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError as e:
            print(f"⚠ Could not record activity: {e}")

    def entries(self):

        out = []

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        entry["_at"] = datetime.fromisoformat(entry["at"])
                        out.append(entry)
                    except (ValueError, KeyError):
                        continue
        except FileNotFoundError:
            pass

        return out

    def prune(self, now=None):
        """Drop activity older than KEEP_DAYS."""

        cutoff = (now or datetime.now()) - timedelta(days=KEEP_DAYS)
        keep = [e for e in self.entries() if e["_at"] >= cutoff]
        self._write(keep)

    def clear(self):
        self._write([])

    def _write(self, entries):
        with open(self.path, "w", encoding="utf-8") as f:
            for e in entries:
                e = {k: v for k, v in e.items() if k != "_at"}
                f.write(json.dumps(e, ensure_ascii=False) + "\n")


# =========================================================
# ROUTINES STORE
# =========================================================

class RoutineStore:

    def __init__(self, path=None):
        self.path = path or user_config_path("routines.json")
        self.load()

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}

        self.routines = data.get("routines", [])
        self.declined = data.get("declined", [])

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(
                {"version": 1, "routines": self.routines, "declined": self.declined},
                f, indent=2, ensure_ascii=False,
            )

    def add(self, suggestion):
        routine = {
            "id": uuid.uuid4().hex[:8],
            "kind": suggestion["kind"],
            "target": suggestion["target"],
            "studio": suggestion.get("studio"),
            "event": suggestion.get("event"),
            "time": suggestion["time"],
            "days": suggestion["days"],
            "enabled": True,
            "created": _time.strftime("%Y-%m-%d"),
            "last_run": None,
        }
        self.routines.append(routine)
        self.save()
        return routine

    def decline(self, suggestion, now=None):
        now = now or datetime.now()
        self.declined = [
            d for d in self.declined
            if not (d["kind"] == suggestion["kind"] and d["target"] == suggestion["target"])
        ]
        self.declined.append({
            "kind": suggestion["kind"],
            "target": suggestion["target"],
            "until": (now + timedelta(days=DECLINE_SNOOZE_DAYS)).date().isoformat(),
        })
        self.save()

    def remove(self, routine_id):
        self.routines = [r for r in self.routines if r["id"] != routine_id]
        self.save()

    def set_enabled(self, routine_id, enabled):
        for r in self.routines:
            if r["id"] == routine_id:
                r["enabled"] = bool(enabled)
        self.save()

    def mark_run(self, routine_id, day):
        for r in self.routines:
            if r["id"] == routine_id:
                r["last_run"] = day.isoformat()
        self.save()

    def is_declined(self, kind, target, now=None):
        today = (now or datetime.now()).date().isoformat()
        return any(
            d["kind"] == kind and d["target"] == target and d["until"] >= today
            for d in self.declined
        )

    def has_routine(self, kind, target):
        return any(r["kind"] == kind and r["target"] == target for r in self.routines)


# =========================================================
# PATTERN DETECTION
# =========================================================

def _minutes(dt):
    return dt.hour * 60 + dt.minute


def format_time(minutes):
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def parse_time(text):
    hours, minutes = text.split(":")
    return int(hours) * 60 + int(minutes)


def describe_days(days):
    days = sorted(days)
    if days == EVERY_DAY:
        return "every day"
    if days == WEEKDAYS:
        return "on weekdays"
    return "on " + ", ".join(DAY_NAMES[d] for d in days)


def suggest_routines(entries, store=None, now=None):
    """
    Routines worth suggesting from activity entries (ActivityLog.entries()).
    Returns a list of suggestions, strongest first:
        {"kind", "target", "studio", "event", "time": "10:00", "days": [...],
         "hits": 5, "of": 6, "message": "..."}
    """

    now = now or datetime.now()

    # Activity entries the user started themselves; routine runs don't count.
    entries = [e for e in entries if e.get("trigger") != "routine"]

    active_days = sorted(
        {e["_at"].date() for e in entries if e["_at"].date() <= now.date()},
        reverse=True,
    )[:LOOKBACK_DAYS]

    if len(active_days) < MIN_DAYS:
        return []

    window = set(active_days)

    # First time each thing happened on each active day.
    first = {}
    details = {}

    for e in sorted(entries, key=lambda e: e["_at"]):
        day = e["_at"].date()
        if day not in window:
            continue
        key = (e["kind"], e["target"])
        first.setdefault(key, {}).setdefault(day, e["_at"])
        details[key] = e

    suggestions = []

    for (kind, target), by_day in first.items():

        if len(by_day) < MIN_DAYS:
            continue

        if store and (store.has_routine(kind, target) or store.is_declined(kind, target, now)):
            continue

        typical = int(statistics.median(_minutes(t) for t in by_day.values()))

        hits = [
            day for day, t in by_day.items()
            if abs(_minutes(t) - typical) <= TIME_WINDOW
        ]

        if len(hits) < MIN_DAYS:
            continue

        rounded = int(round(typical / 5.0) * 5) % (24 * 60)

        weekdays_only = all(day.weekday() < 5 for day in hits)
        days = WEEKDAYS if weekdays_only else EVERY_DAY

        sample = details[(kind, target)]
        what = {
            "studio": f"open {target}",
            "launch": f"launch {target}",
        }.get(kind, f'run "{target}"')

        suggestions.append({
            "kind": kind,
            "target": target,
            "studio": sample.get("studio"),
            "event": sample.get("event"),
            "time": format_time(rounded),
            "days": days,
            "hits": len(hits),
            "of": len(active_days),
            "message": (
                f"You usually {what} around {format_time(rounded)}. "
                f"Do it automatically {describe_days(days)}?"
            ),
        })

    suggestions.sort(key=lambda s: (-s["hits"], s["time"]))
    return suggestions


# =========================================================
# SCHEDULING
# =========================================================

def due_routines(routines, now=None):
    """Routines that should run now (each at most once a day)."""

    now = now or datetime.now()
    today = now.date().isoformat()
    minutes = _minutes(now)

    due = []

    for r in routines:

        if not r.get("enabled", True):
            continue

        if now.weekday() not in r.get("days", EVERY_DAY):
            continue

        if r.get("last_run") == today:
            continue

        start = parse_time(r["time"])

        if start <= minutes <= start + RUN_GRACE_MINUTES:
            due.append(r)

    return due

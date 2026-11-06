import os
import tempfile
import unittest
from datetime import datetime, timedelta

from backend.routines import (
    ActivityLog,
    RoutineStore,
    due_routines,
    suggest_routines,
)

# A Thursday, so the previous days include a weekend.
NOW = datetime(2026, 11, 5, 9, 0)


class Base(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.log = ActivityLog(os.path.join(self.tmp.name, "activity.jsonl"))
        self.store = RoutineStore(os.path.join(self.tmp.name, "routines.json"))

    def open_studio(self, day_offset, hour, minute, target="Test Studio", trigger="click"):
        when = (NOW - timedelta(days=day_offset)).replace(hour=hour, minute=minute)
        self.log.record("studio", target, studio=target, trigger=trigger, when=when)

    def suggestions(self, now=NOW):
        return suggest_routines(self.log.entries(), self.store, now)


class SuggestTests(Base):

    def test_weekday_habit_is_suggested(self):
        # Last 7 weekdays (skipping the weekend) around 10:00
        for offset, (h, m) in zip([1, 2, 3, 6, 7, 8, 9], [(10, 2), (9, 55), (10, 10), (10, 0), (9, 58), (10, 5), (11, 30)]):
            self.open_studio(offset, h, m)
        s = self.suggestions()
        self.assertEqual(len(s), 1)
        self.assertEqual(s[0]["target"], "Test Studio")
        self.assertEqual(s[0]["time"], "10:00")
        self.assertEqual(s[0]["days"], [0, 1, 2, 3, 4])
        self.assertIn("on weekdays", s[0]["message"])

    def test_random_times_are_not_a_habit(self):
        for offset, h in zip(range(1, 8), [8, 11, 14, 17, 9, 20, 13]):
            self.open_studio(offset, h, 0)
        self.assertEqual(self.suggestions(), [])

    def test_needs_enough_days(self):
        for offset in (1, 2, 3):
            self.open_studio(offset, 10, 0)
        self.assertEqual(self.suggestions(), [])

    def test_days_without_lensflow_do_not_count_against_a_habit(self):
        # Used only 4 days in the last two weeks, always at 10:00.
        for offset in (1, 4, 9, 13):
            self.open_studio(offset, 10, 0)
        self.assertEqual(len(self.suggestions()), 1)

    def test_every_day_habit_includes_weekends(self):
        for offset in range(1, 8):
            self.open_studio(offset, 21, 0, target="Gaming Studio")
        s = self.suggestions()
        self.assertEqual(s[0]["days"], [0, 1, 2, 3, 4, 5, 6])

    def test_declined_and_accepted_are_not_suggested_again(self):
        for offset in range(1, 8):
            self.open_studio(offset, 10, 0)
        s = self.suggestions()[0]
        self.store.decline(s, now=NOW)
        self.assertEqual(self.suggestions(), [])
        # ...until the snooze ends
        self.assertEqual(len(self.suggestions(now=NOW + timedelta(days=31))), 1)
        self.store.add(s)
        self.assertEqual(self.suggestions(now=NOW + timedelta(days=31)), [])

    def test_routine_runs_are_ignored(self):
        for offset in range(1, 8):
            self.open_studio(offset, 10, 0, trigger="routine")
        self.assertEqual(self.suggestions(), [])


class DueTests(Base):

    def routine(self, **kw):
        r = {"id": "r1", "time": "10:00", "days": [0, 1, 2, 3, 4], "enabled": True, "last_run": None}
        r.update(kw)
        return r

    def test_runs_in_its_window_once_a_day(self):
        thursday_10_05 = datetime(2026, 11, 5, 10, 5)
        self.assertEqual(len(due_routines([self.routine()], thursday_10_05)), 1)
        self.assertEqual(due_routines([self.routine(last_run="2026-11-05")], thursday_10_05), [])

    def test_not_before_or_long_after(self):
        self.assertEqual(due_routines([self.routine()], datetime(2026, 11, 5, 9, 59)), [])
        self.assertEqual(due_routines([self.routine()], datetime(2026, 11, 5, 10, 31)), [])

    def test_respects_days_and_enabled(self):
        saturday = datetime(2026, 11, 7, 10, 0)
        self.assertEqual(due_routines([self.routine()], saturday), [])
        self.assertEqual(due_routines([self.routine(enabled=False)], datetime(2026, 11, 5, 10, 0)), [])


class LogTests(Base):

    def test_prune_and_clear(self):
        self.open_studio(100, 10, 0)
        self.open_studio(1, 10, 0)
        self.log.prune(now=NOW)
        self.assertEqual(len(self.log.entries()), 1)
        self.log.clear()
        self.assertEqual(self.log.entries(), [])

    def test_corrupt_lines_are_skipped(self):
        self.open_studio(1, 10, 0)
        with open(self.log.path, "a") as f:
            f.write("{oops\n")
        self.assertEqual(len(self.log.entries()), 1)


if __name__ == "__main__":
    unittest.main()

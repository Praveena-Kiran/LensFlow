import unittest
from unittest import mock

from backend.automation.events import (
    events_for_gesture,
    gesture_of,
    parse_hotkey,
    powerpoint_command,
    profile_events,
    trigger_of,
)


class TriggerTests(unittest.TestCase):

    def test_legacy_gesture_field(self):
        self.assertEqual(gesture_of({"gesture": "Point"}), "Point")
        self.assertEqual(trigger_of({"gesture": "  "}), {"type": "manual"})
        self.assertIsNone(gesture_of({"name": "click only"}))

    def test_explicit_trigger_wins(self):
        event = {"gesture": "old", "trigger": {"type": "gesture", "gesture": "new"}}
        self.assertEqual(gesture_of(event), "new")

    def test_events_for_gesture_keeps_order_and_ignores_none(self):
        events = [
            {"name": "a", "gesture": "Point"},
            {"name": "b", "gesture": ""},
            {"name": "c", "gesture": "Point"},
        ]
        self.assertEqual([e["name"] for e in events_for_gesture(events, "Point")], ["a", "c"])
        self.assertEqual(events_for_gesture(events, None), [])


class ProfileTests(unittest.TestCase):

    def test_presentation_profile_becomes_events(self):
        profile = {"gesture_map": {
            "👍 Thumbs Up": "presentation_next",
            "✋ Open Palm": "ACTIVATE",
            "✌️ Peace": "coding_flow",
        }}
        events = {e["gesture"]: e for e in profile_events(profile)}
        self.assertEqual(events["👍 Thumbs Up"]["action"], "PowerPoint")
        self.assertEqual(events["👍 Thumbs Up"]["value"], "next")
        self.assertEqual(events["✋ Open Palm"]["action"], "LensFlow")
        self.assertEqual(events["✌️ Peace"], {
            "name": "coding_flow", "gesture": "✌️ Peace",
            "action": "Run Flow", "value": "coding_flow",
        })

    def test_empty_profile(self):
        self.assertEqual(profile_events(None), [])


class ValueParsingTests(unittest.TestCase):

    def test_hotkeys(self):
        self.assertEqual(parse_hotkey("Ctrl + Shift + T"), ["ctrl", "shift", "t"])
        with self.assertRaises(ValueError):
            parse_hotkey(" + ")

    def test_powerpoint(self):
        self.assertEqual(powerpoint_command("Next"), "next_slide")
        self.assertEqual(powerpoint_command("prev"), "previous_slide")
        with self.assertRaises(ValueError):
            powerpoint_command("sideways")


class RunnerTests(unittest.TestCase):
    """FlowManager.execute_custom_event dispatches to the right action."""

    def setUp(self):
        import os, tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        patcher = mock.patch.dict(os.environ, {"LENSFLOW_DATA_DIR": self.tmp.name})
        patcher.start()
        self.addCleanup(patcher.stop)

        from backend.automation.flow_manager import FlowManager
        self.fm = FlowManager()
        self.fm.actions["hotkey"] = mock.Mock()
        self.fm.actions["powerpoint"] = mock.Mock()

    def run_event(self, action, value):
        self.fm.execute_custom_event({"name": "t", "action": action, "value": value})

    def test_hotkey(self):
        self.run_event("Hotkey", "ctrl+shift+t")
        self.fm.actions["hotkey"].execute.assert_called_once_with({"keys": ["ctrl", "shift", "t"]})

    def test_powerpoint(self):
        self.run_event("PowerPoint", "next")
        self.assertEqual(
            self.fm.actions["powerpoint"].execute.call_args[0][0],
            {"command": "next_slide"},
        )

    def test_run_flow(self):
        with mock.patch.object(self.fm, "execute_flow") as run:
            self.run_event("Run Flow", "coding_flow")
        run.assert_called_once_with("coding_flow")
        with self.assertRaises(ValueError):
            self.run_event("Run Flow", "no_such_flow")

    def test_errors_are_raised_not_swallowed(self):
        for action, value in [
            ("Open File", "/definitely/missing.txt"),
            ("Open Website", ""),
            ("Wait", "soon"),
            ("Teleport", "x"),
        ]:
            with self.assertRaises(Exception, msg=action):
                self.run_event(action, value)

    def test_website_gets_scheme(self):
        with mock.patch("webbrowser.open", return_value=True) as open_:
            self.run_event("Open Website", "github.com")
        open_.assert_called_once_with("https://github.com")

    def test_flow_keeps_going_and_reports_failures(self):
        ran = []
        ok = mock.Mock(execute=lambda step, apps: ran.append(step["label"]))
        bad = mock.Mock(execute=mock.Mock(side_effect=RuntimeError("not installed")))
        self.fm.actions = {"ok": ok, "bad": bad}
        self.fm.flows = {"f": {"name": "F", "actions": [
            {"type": "bad", "label": "VS Code"},
            {"type": "ok", "label": "GitHub"},
        ]}}
        with self.assertRaises(RuntimeError) as ctx:
            self.fm.execute_flow("f")
        self.assertEqual(ran, ["GitHub"])
        self.assertIn("VS Code: not installed", str(ctx.exception))
        with self.assertRaises(ValueError):
            self.fm.execute_flow("missing")

    def test_lensflow_action_is_a_noop(self):
        self.run_event("LensFlow", "activate")


if __name__ == "__main__":
    unittest.main()

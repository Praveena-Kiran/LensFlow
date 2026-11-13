import math
import os
import tempfile
import unittest
from unittest import mock

from backend.automation.triggers import (
    CUSTOM_MOTION,
    GESTURE,
    MISSING,
    MOTION,
    catalogue,
    trigger_kind,
    triggers_by_action,
)


class TriggerLogicTests(unittest.TestCase):

    def test_kinds(self):
        self.assertEqual(trigger_kind("👍 Thumbs Up"), GESTURE)
        self.assertEqual(trigger_kind("Swipe right"), MOTION)
        self.assertEqual(trigger_kind("forward", custom_motions=["forward"]), CUSTOM_MOTION)
        self.assertEqual(trigger_kind("forward"), MISSING)

    def test_catalogue_groups_and_skips_empty(self):
        groups = dict(catalogue([], ["forward"]))
        self.assertIn("Hand gestures", groups)
        self.assertIn("Swipe left", groups["Motions"])
        self.assertEqual(groups["Your motions"], ["forward"])
        self.assertNotIn("Your gestures", groups)

    def test_mixed_triggers_per_action(self):
        grouped = triggers_by_action(
            {"👍 Thumbs Up": "presentation_next", "forward": "presentation_next",
             "Swipe left": "presentation_previous", "x": "other"},
            ["presentation_next", "presentation_previous", "presentation_end"],
        )
        self.assertEqual(grouped["presentation_next"], ["👍 Thumbs Up", "forward"])
        self.assertEqual(grouped["presentation_previous"], ["Swipe left"])
        self.assertEqual(grouped["presentation_end"], [])


class TriggerEditorTests(unittest.TestCase):
    """The Gesture Studio editor, headless (Qt offscreen)."""

    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        env = mock.patch.dict(os.environ, {"WIELD_DATA_DIR": self.tmp.name})
        env.start()
        self.addCleanup(env.stop)
        self.addCleanup(self.tmp.cleanup)

        from backend.gestures.motions import MotionStore, normalize_trajectory
        from backend.profile_manager import ProfileManager
        from frontend.components.trigger_editor import ActionTriggerEditor

        def arc(seed):
            return [(0.3 + 0.3 * i / 19, 0.5 - 0.12 * math.sin(math.pi * i / 19) + 0.002 * seed)
                    for i in range(20)]

        MotionStore().add("forward", [normalize_trajectory(arc(s)) for s in range(3)])

        self.pm = ProfileManager()
        self.pm.load("presentation")
        self.editor = ActionTriggerEditor(
            self.pm,
            ["presentation_start", "presentation_next", "presentation_previous", "presentation_end"],
            custom_gestures=lambda: [],
            custom_motions=lambda: MotionStore().names(),
        )

    def tearDown(self):
        # Destroy Qt widgets now: leaving them for interpreter shutdown
        # crashes PySide intermittently.
        from PySide6.QtCore import QCoreApplication, QEvent
        for widget in getattr(self, "_widgets", []) + [self.editor]:
            widget.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()

    def keep(self, widget):
        self._widgets = getattr(self, "_widgets", []) + [widget]
        return widget

    def triggers(self, action):
        return self.editor.rows[action].triggers

    def test_add_motion_alongside_gesture(self):
        self.editor.assign("forward", "presentation_next")
        self.assertIn("forward", self.triggers("presentation_next"))
        self.assertIn("👍 Thumbs Up", self.triggers("presentation_next"))

        # Saved: a fresh load sees both.
        from backend.profile_manager import ProfileManager
        pm = ProfileManager()
        pm.load("presentation")
        self.assertEqual(pm.get_gesture_map()["forward"], "presentation_next")

    def test_assigning_used_trigger_moves_it(self):
        self.editor.assign("👍 Thumbs Up", "presentation_previous")
        self.assertNotIn("👍 Thumbs Up", self.triggers("presentation_next"))
        self.assertIn("👍 Thumbs Up", self.triggers("presentation_previous"))

    def test_remove_trigger(self):
        self.editor.remove_trigger("👍 Thumbs Up")
        self.assertNotIn("👍 Thumbs Up", self.triggers("presentation_next"))
        self.assertNotIn("👍 Thumbs Up", self.pm.get_gesture_map())

    def test_picker_lists_motions_and_marks_used(self):
        from frontend.components.trigger_editor import TriggerPickerDialog

        self.editor.assign("forward", "presentation_previous")
        dialog = self.keep(TriggerPickerDialog(
            "presentation_next", self.pm.get_gesture_map(), [], ["forward"]
        ))
        names = [dialog.box.itemData(i) for i in range(dialog.box.count())]
        labels = [dialog.box.itemText(i) for i in range(dialog.box.count())]

        self.assertIn("forward", names)
        self.assertIn("Swipe up", names)
        # Already on this action -> not offered again.
        self.assertNotIn("👍 Thumbs Up", names)
        self.assertTrue(any("forward" in l and "Previous slide" in l for l in labels))
        # Group headings are not selectable.
        self.assertIn("YOUR MOTIONS", labels)
        self.assertIsNotNone(dialog.selected())

    def test_picker_custom_voice_phrase(self):
        from frontend.components.trigger_editor import CUSTOM_PHRASE, TriggerPickerDialog

        dialog = self.keep(TriggerPickerDialog(
            "presentation_next", self.pm.get_gesture_map(), [], []
        ))
        index = dialog.box.findData(CUSTOM_PHRASE)
        self.assertGreaterEqual(index, 0)
        dialog.box.setCurrentIndex(index)

        dialog.phrase_input.setText("go")                 # too short
        self.assertIsNone(dialog.selected())
        self.assertFalse(dialog.ok_button.isEnabled())

        dialog.phrase_input.setText("Next one, please!")
        self.assertEqual(dialog.selected(), "🎤 next one please")
        self.assertTrue(dialog.ok_button.isEnabled())

        self.editor.assign(dialog.selected(), "presentation_next")
        self.assertIn("🎤 next one please", self.triggers("presentation_next"))


if __name__ == "__main__":
    unittest.main()

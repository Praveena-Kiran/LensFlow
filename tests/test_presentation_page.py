import os
import tempfile
import unittest
from unittest import mock

try:
    import PySide6  # noqa: F401
    HAVE_QT = True
except ImportError:  # CI's unit-test job installs only the standard library
    HAVE_QT = False


@unittest.skipUnless(HAVE_QT, "PySide6 not installed")
class PresentationPageTests(unittest.TestCase):

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

        from frontend.pages.presentation_page import PresentationPage
        self.page = PresentationPage()
        self.changes = []
        self.page.bindings_changed.connect(lambda: self.changes.append(1))

    def tearDown(self):
        from PySide6.QtCore import QCoreApplication, QEvent
        self.page.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()

    def saved_map(self):
        from backend.profile_manager import ProfileManager
        pm = ProfileManager()
        pm.load("presentation")
        return pm.get_gesture_map()

    def choose(self, action, gesture):
        combo = self.page.rows[action].gesture
        combo.setCurrentIndex(combo.findData(gesture))

    def test_rows_show_saved_gestures_and_phrases(self):
        row = self.page.rows["presentation_next"]
        self.assertEqual(row.gesture.currentData(), "👍 Thumbs Up")
        self.assertEqual(row.phrase.text(), "next slide")

    def test_choosing_a_gesture_saves_and_moves_it(self):
        self.choose("presentation_end", "👎 Thumbs Down")
        saved = self.saved_map()
        self.assertEqual(saved["👎 Thumbs Down"], "presentation_end")
        self.assertNotIn("✊ Fist", saved)                 # replaced
        self.assertTrue(self.changes)
        # Previous slide lost it and now shows its next gesture.
        self.assertNotEqual(
            self.page.rows["presentation_previous"].gesture.currentData(), "👎 Thumbs Down"
        )
        self.assertIn("Previous slide", self.page.rows["presentation_end"].hint.text())

    def test_no_gesture(self):
        self.choose("presentation_start", None)
        self.assertNotIn("✌️ Peace", self.saved_map())

    def test_typing_a_phrase_saves_when_done(self):
        row = self.page.rows["presentation_next"]
        row.phrase.setText("Onwards, please!")
        self.assertEqual(self.saved_map().get("🎤 next slide"), "presentation_next")  # not yet
        row.phrase.editingFinished.emit()
        saved = self.saved_map()
        self.assertEqual(saved["🎤 onwards please"], "presentation_next")
        self.assertNotIn("🎤 next slide", saved)
        self.assertEqual(row.phrase.text(), "onwards please")

    def test_invalid_phrase_is_flagged_and_not_saved(self):
        row = self.page.rows["presentation_end"]
        row.phrase.setText("next slide")                 # used by Next slide
        self.assertTrue(row.phrase.property("invalid"))
        self.assertIn("already used", row.hint.text())
        row.phrase.editingFinished.emit()
        self.assertEqual(self.saved_map()["🎤 next slide"], "presentation_next")
        self.assertEqual(self.saved_map()["🎤 end presentation"], "presentation_end")

    def test_clearing_a_phrase_removes_voice_for_that_action(self):
        row = self.page.rows["presentation_previous"]
        row.phrase.setText("")
        row.phrase.editingFinished.emit()
        self.assertNotIn("🎤 previous slide", self.saved_map())

    def test_voice_off_note(self):
        from backend.settings import gesture_settings
        gesture_settings.save("voice_enabled", False)
        self.page.refresh_bindings()
        self.assertIn("Settings", self.page.voice_note.text())
        gesture_settings.save("voice_enabled", True)
        self.page.refresh_bindings()
        self.assertTrue(self.page.voice_note.isHidden())

    def test_gesture_studio_sees_changes_and_does_not_undo_them(self):
        from frontend.pages.gesture_page import GesturePage

        gesture_page = GesturePage()
        try:
            self.choose("presentation_end", "☝️ Pointing Up")
            gesture_page.refresh_gesture_list()
            self.assertIn(
                "☝️ Pointing Up",
                gesture_page.trigger_editor.rows["presentation_end"].triggers,
            )
            # An edit in Gesture Studio keeps the Presentation Studio change.
            gesture_page.trigger_editor.assign("Swipe up", "presentation_start")
            saved = self.saved_map()
            self.assertEqual(saved["☝️ Pointing Up"], "presentation_end")
            self.assertEqual(saved["Swipe up"], "presentation_start")
        finally:
            gesture_page.deleteLater()


if __name__ == "__main__":
    unittest.main()

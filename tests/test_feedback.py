import os
import tempfile
import unittest
import wave
from unittest import mock

try:
    import PySide6  # noqa: F401
    HAVE_QT = True
except ImportError:  # CI's unit-test job installs only the standard library
    HAVE_QT = False

from backend.feedback.sounds import CUES, SoundCues


class SoundCueTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.played = []
        self.t = 0.0
        self.sounds = SoundCues(
            folder=self.tmp.name,
            player=self.played.append,
            clock=lambda: self.t,
        )

    def test_generates_valid_short_wavs(self):
        self.sounds.ensure_files()
        for cue in CUES:
            with wave.open(self.sounds.path(cue)) as w:
                self.assertEqual(w.getnchannels(), 1)
                seconds = w.getnframes() / w.getframerate()
                self.assertGreater(seconds, 0.05)
                self.assertLess(seconds, 0.5)

    def test_plays_and_respects_switch(self):
        self.assertTrue(self.sounds.play("action"))
        self.assertEqual(self.played, [self.sounds.path("action")])
        self.sounds.enabled = False
        self.t += 1
        self.assertFalse(self.sounds.play("action"))
        self.assertEqual(len(self.played), 1)

    def test_same_cue_is_not_repeated_instantly(self):
        self.sounds.play("action")
        self.assertFalse(self.sounds.play("action"))
        self.t += 0.5
        self.assertTrue(self.sounds.play("action"))

    def test_unknown_cue_and_no_player(self):
        self.assertFalse(self.sounds.play("nope"))
        silent = SoundCues(folder=self.tmp.name, player=None)
        self.assertFalse(silent.play("action"))

    def test_player_errors_are_swallowed(self):
        def broken(path):
            raise OSError("no audio device")
        sounds = SoundCues(folder=self.tmp.name, player=broken)
        self.assertFalse(sounds.play("error"))


@unittest.skipUnless(HAVE_QT, "PySide6 not installed")
class FeedbackTests(unittest.TestCase):

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

        from frontend.components.feedback_overlay import Feedback, FeedbackOverlay

        self.window = mock.Mock()
        self.window.isActiveWindow.return_value = False
        self.played = []
        self.overlay = FeedbackOverlay()
        self.feedback = Feedback(
            self.window,
            overlay=self.overlay,
            sounds=SoundCues(folder=self.tmp.name, player=self.played.append),
        )

    def tearDown(self):
        from PySide6.QtCore import QCoreApplication, QEvent
        self.overlay.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()

    def test_action_plays_sound_and_shows_note(self):
        self.feedback.action("👍 Thumbs Up", "Next slide")
        self.assertTrue(self.played)
        self.assertTrue(self.overlay.isVisible())
        self.assertIn("Next slide", self.overlay.label.text())

    def test_no_note_when_wield_is_in_front(self):
        self.window.isActiveWindow.return_value = True
        self.feedback.action("👍 Thumbs Up", "Next slide")
        self.assertFalse(self.overlay.isVisible())
        self.assertTrue(self.played)   # the sound still plays

    def test_armed_note_stays_until_disarmed(self):
        self.feedback.armed("✋ Open Palm")
        self.assertEqual(self.overlay.kind, "armed")
        self.assertFalse(self.overlay._hide_timer.isActive())
        self.feedback.disarmed()
        self.assertFalse(self.overlay._hide_timer.isActive())

    def test_settings_switch_off_sound_and_note(self):
        from backend.settings import gesture_settings
        gesture_settings.save("sound_feedback", False)
        gesture_settings.save("feedback_overlay", False)
        self.feedback.action("👍 Thumbs Up", "Next slide")
        self.assertEqual(self.played, [])
        self.assertFalse(self.overlay.isVisible())

    def test_failure_uses_error_note(self):
        self.feedback.failed("Next slide", "PowerPoint isn't open")
        self.assertEqual(self.overlay.kind, "error")
        self.assertIn("didn't work", self.overlay.label.text())


if __name__ == "__main__":
    unittest.main()

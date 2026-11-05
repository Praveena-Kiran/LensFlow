import unittest

from backend.gestures.gesture_stabilizer import GestureStabilizer


class StabilizerTests(unittest.TestCase):

    def test_triggers_once_while_gesture_is_held(self):
        s = GestureStabilizer()
        results = [s.update("👍 Thumbs Up", 0.9) for _ in range(5)]
        self.assertEqual(results.count("👍 Thumbs Up"), 1)

    def test_same_gesture_triggers_again_after_hand_relaxes(self):
        s = GestureStabilizer(window_size=3)
        self.assertEqual(s.update("👍 Thumbs Up", 0.9), "👍 Thumbs Up")
        for _ in range(3):
            s.update(None, 0.0)
        self.assertEqual(s.update("👍 Thumbs Up", 0.9), "👍 Thumbs Up")

    def test_brief_dropout_does_not_retrigger(self):
        s = GestureStabilizer(window_size=3)
        s.update("👍 Thumbs Up", 0.9)
        s.update(None, 0.0)  # one missed frame
        self.assertIsNone(s.update("👍 Thumbs Up", 0.9))

    def test_low_confidence_is_ignored(self):
        self.assertIsNone(GestureStabilizer().update("👍 Thumbs Up", 0.3))


if __name__ == "__main__":
    unittest.main()

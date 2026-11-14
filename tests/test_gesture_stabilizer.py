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


class HoldTimeTests(unittest.TestCase):

    def make(self, hold):
        self.now = 0.0
        return GestureStabilizer(hold_time=hold, clock=lambda: self.now)

    def step(self, s, gesture, dt=0.1):
        self.now += dt
        return s.update(gesture, 0.9 if gesture else 0.0)

    def test_must_hold_before_triggering(self):
        s = self.make(0.5)
        results = [self.step(s, "Point") for _ in range(8)]   # 0.1 .. 0.8 s
        self.assertEqual(results.count("Point"), 1)
        self.assertEqual(results.index("Point"), 5)           # held 0.5 s

    def test_letting_go_restarts_the_hold(self):
        s = self.make(0.5)
        for _ in range(3):
            self.assertIsNone(self.step(s, "Point"))
        self.assertIsNone(self.step(s, None))
        for _ in range(5):   # held 0.0 .. 0.4 s
            self.assertIsNone(self.step(s, "Point"))
        self.assertEqual(self.step(s, "Point"), "Point")

    def test_switching_gesture_restarts_the_hold(self):
        s = self.make(0.3)
        self.step(s, "A"); self.step(s, "A")
        self.assertIsNone(self.step(s, "B"))
        self.assertIsNone(self.step(s, "B"))
        self.assertIsNone(self.step(s, "B"))
        self.assertEqual(self.step(s, "B"), "B")


if __name__ == "__main__":
    unittest.main()

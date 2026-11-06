import math
import unittest

from backend.fog import fingertip, hand_mode


def hand(extended):
    """Synthetic landmarks: wrist at the bottom, fingers pointing up.
    `extended` = set of finger names that are out."""
    pts = [(0.5, 0.9)] + [(0.5, 0.8)] * 20
    bases = {"index": (0.42, 5, 6, 7, 8), "middle": (0.48, 9, 10, 11, 12),
             "ring": (0.54, 13, 14, 15, 16), "pinky": (0.60, 17, 18, 19, 20)}
    for name, (x, mcp, pip, dip, tip) in bases.items():
        pts[mcp] = (x, 0.7)
        pts[pip] = (x, 0.6)
        if name in extended:
            pts[dip], pts[tip] = (x, 0.5), (x, 0.4)
        else:  # curled back down towards the palm
            pts[dip], pts[tip] = (x, 0.65), (x, 0.72)
    pts[4] = (0.35, 0.75)
    return [(x, y, 0.0) for x, y in pts]


class HandModeTests(unittest.TestCase):

    def test_modes(self):
        self.assertEqual(hand_mode(hand({"index"})), "write")
        self.assertEqual(hand_mode(hand(set())), "pause")
        self.assertEqual(hand_mode(hand({"index", "middle", "ring", "pinky"})), "wipe")
        self.assertIsNone(hand_mode(hand({"index", "middle"})))   # peace sign
        self.assertIsNone(hand_mode(None))

    def test_fingertip(self):
        self.assertEqual(fingertip(hand({"index"}))[:2], (0.42, 0.4))
        self.assertIsNone(fingertip(None))


if __name__ == "__main__":
    unittest.main()

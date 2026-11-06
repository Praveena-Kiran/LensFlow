import math
import os
import random
import tempfile
import unittest

from backend.gestures.motions import (
    MotionMatcher,
    MotionSegmenter,
    MotionStore,
    RESAMPLE_POINTS,
    dtw_distance,
    normalize_trajectory,
    palm_point,
    path_length,
    resample,
    review_motion,
)


def noisy(points, amount=0.01, seed=0):
    rng = random.Random(seed)
    return [(x + rng.gauss(0, amount), y + rng.gauss(0, amount)) for x, y in points]


def line(dx, dy, n=20, x0=0.5, y0=0.5):
    return [(x0 + dx * i / (n - 1), y0 + dy * i / (n - 1)) for i in range(n)]


def wave(n=40, width=0.3, height=0.08, cycles=1.5):
    return [(0.5 + width * i / (n - 1), 0.5 + height * math.sin(2 * math.pi * cycles * i / (n - 1))) for i in range(n)]


def circle(n=40, r=0.1):
    return [(0.5 + r * math.cos(2 * math.pi * i / (n - 1)), 0.5 + r * math.sin(2 * math.pi * i / (n - 1))) for i in range(n)]


class NormaliseTests(unittest.TestCase):

    def test_resample_length_and_spacing(self):
        # Uneven input spacing on a straight path -> even output spacing.
        pts = resample([(0, 0), (0.1, 0), (0.15, 0), (1, 0), (2, 0)])
        self.assertEqual(len(pts), RESAMPLE_POINTS)
        gaps = [b[0] - a[0] for a, b in zip(pts, pts[1:])]
        self.assertAlmostEqual(min(gaps), max(gaps), places=6)
        self.assertAlmostEqual(pts[-1][0], 2.0, places=6)

    def test_size_position_and_speed_invariant(self):
        small_fast = normalize_trajectory(line(0.2, 0, n=5))
        big_slow = normalize_trajectory(line(0.6, 0, n=60, x0=0.1, y0=0.9))
        self.assertLess(dtw_distance(small_fast, big_slow), 1e-6)

    def test_degenerate(self):
        self.assertIsNone(normalize_trajectory([(0.5, 0.5)] * 5))
        self.assertIsNone(normalize_trajectory([]))


class MatcherTests(unittest.TestCase):

    def test_builtin_swipes_with_noise(self):
        m = MotionMatcher()
        for name, (dx, dy) in {
            "Swipe right": (0.4, 0.03), "Swipe left": (-0.4, -0.02),
            "Swipe up": (0.02, -0.35), "Swipe down": (-0.03, 0.35),
        }.items():
            got, conf = m.match_trajectory(normalize_trajectory(noisy(line(dx, dy), 0.004)))
            self.assertEqual(got, name)
            self.assertGreaterEqual(conf, 0.6)

    def test_custom_wave_and_circle(self):
        motions = [
            {"name": "Wave", "samples": [normalize_trajectory(noisy(wave(), 0.003, s)) for s in range(3)]},
            {"name": "Circle", "samples": [normalize_trajectory(noisy(circle(), 0.003, s)) for s in range(3)]},
        ]
        m = MotionMatcher(motions)
        self.assertEqual(m.match_trajectory(normalize_trajectory(noisy(wave(), 0.003, 9)))[0], "Wave")
        self.assertEqual(m.match_trajectory(normalize_trajectory(noisy(circle(r=0.2), 0.004, 9)))[0], "Circle")
        # A plain swipe is not mistaken for the wave.
        self.assertEqual(m.match_trajectory(normalize_trajectory(line(0.3, 0)))[0], "Swipe right")

    def test_tilted_and_curved_swipes_match_but_l_shapes_do_not(self):
        m = MotionMatcher()
        a = math.radians(20)
        self.assertEqual(m.match_trajectory(normalize_trajectory(noisy(line(0.4 * math.cos(a), 0.4 * math.sin(a)), 0.004)))[0], "Swipe right")
        arc = [(0.3 + 0.4 * i / 19, 0.5 - 0.1 * math.sin(math.pi * i / 19)) for i in range(20)]
        self.assertEqual(m.match_trajectory(normalize_trajectory(arc))[0], "Swipe right")
        for shape in (line(0.3, 0) + line(0, 0.3, x0=0.8), wave(height=0.08), circle(),
                      line(0.3, 0) + line(-0.3, 0, x0=0.8)):
            self.assertIsNone(m.match_trajectory(normalize_trajectory(shape))[0])

    def test_diagonal_is_not_a_swipe(self):
        self.assertIsNone(MotionMatcher().match_trajectory(normalize_trajectory(line(0.3, 0.3)))[0])

    def test_random_scribble_rejected(self):
        rng = random.Random(3)
        scribble = [(rng.random(), rng.random()) for _ in range(30)]
        self.assertEqual(MotionMatcher().match_trajectory(normalize_trajectory(scribble)), (None, 0.0))


class SegmenterTests(unittest.TestCase):

    def feed(self, seg, track, t0=0.0, fps=30):
        out = []
        for i, p in enumerate(track):
            r = seg.update(t0 + i / fps, p)
            if r:
                out.append(r)
        return out

    def test_detects_one_swipe_between_still_periods(self):
        size = 0.1
        still = [(0.3, 0.5, size)] * 10
        move = [(0.3 + 0.02 * i, 0.5, size) for i in range(1, 16)]   # 0.3 units in 0.5 s = 6 palms/s
        rest = [(0.6, 0.5, size)] * 10
        strokes = self.feed(MotionSegmenter(), still + move + rest)
        self.assertEqual(len(strokes), 1)
        self.assertEqual(MotionMatcher().match_stroke(strokes[0])[0], "Swipe right")

    def test_small_jitter_is_not_a_stroke(self):
        rng = random.Random(1)
        track = [(0.5 + rng.gauss(0, 0.002), 0.5 + rng.gauss(0, 0.002), 0.1) for _ in range(60)]
        self.assertEqual(self.feed(MotionSegmenter(), track), [])

    def test_hand_leaving_ends_stroke(self):
        move = [(0.2 + 0.03 * i, 0.5, 0.1) for i in range(12)]
        strokes = self.feed(MotionSegmenter(), move + [None])
        self.assertEqual(len(strokes), 1)

    def test_active_flag(self):
        seg = MotionSegmenter()
        seg.update(0.0, (0.2, 0.5, 0.1))
        self.assertFalse(seg.active)
        seg.update(0.033, (0.25, 0.5, 0.1))
        self.assertTrue(seg.active)


class PalmPointTests(unittest.TestCase):

    def test_aspect_and_size(self):
        lms = [(0.5, 0.5, 0)] * 21
        lms = list(lms)
        lms[9] = (0.5, 0.4, 0)
        x, y, size = palm_point(lms, aspect=2.0)
        self.assertAlmostEqual(size, 0.1)
        self.assertAlmostEqual(x, 1.0)
        self.assertIsNone(palm_point(None))


class StoreAndReviewTests(unittest.TestCase):

    def test_store_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "m.json")
            s = MotionStore(path)
            s.add("Wave", [normalize_trajectory(wave())])
            self.assertEqual(MotionStore(path).names(), ["Wave"])
            self.assertTrue(MotionStore(path).delete("Wave"))

    def test_review(self):
        takes = [normalize_trajectory(noisy(wave(), 0.003, s)) for s in range(3)]
        self.assertTrue(review_motion("Wave", takes, [], [])[0])
        self.assertFalse(review_motion("", takes, [], [])[0])
        self.assertFalse(review_motion("Swipe left", takes, [], [])[0])
        self.assertFalse(review_motion("Wave", takes[:1], [], [])[0])
        inconsistent = [takes[0], normalize_trajectory(circle())]
        self.assertFalse(review_motion("Wave", inconsistent, [], [])[0])
        swipes = [normalize_trajectory(noisy(line(0.4, 0), 0.003, s)) for s in range(3)]
        ok, msg = review_motion("My swipe", swipes, [], [])
        self.assertFalse(ok)
        self.assertIn("swipe right", msg)


if __name__ == "__main__":
    unittest.main()


class RecognizerTests(unittest.TestCase):

    def run_track(self, track, fps=30):
        from backend.gestures.motions import MotionRecognizer
        rec = MotionRecognizer()
        out = []
        for i, p in enumerate(track):
            r = rec.update(i / fps, p)
            if r:
                out.append(r[0])
        return out

    def test_return_movement_after_swipe_is_ignored(self):
        size = 0.1
        still = lambda x, n: [(x, 0.5, size)] * n
        right = [(0.3 + 0.02 * i, 0.5, size) for i in range(1, 16)]
        back = [(0.6 - 0.02 * i, 0.5, size) for i in range(1, 16)]
        # swipe right, short pause, hand comes back: one swipe only
        self.assertEqual(self.run_track(still(0.3, 10) + right + still(0.6, 5) + back + still(0.3, 10)),
                         ["Swipe right"])
        # ...but a deliberate swipe left after a longer pause still counts
        self.assertEqual(self.run_track(still(0.3, 10) + right + still(0.6, 30) + back + still(0.3, 10)),
                         ["Swipe right", "Swipe left"])

    def test_two_swipes_same_direction(self):
        size = 0.1
        right = lambda x0: [(x0 + 0.02 * i, 0.5, size) for i in range(1, 16)]
        still = lambda x, n: [(x, 0.5, size)] * n
        track = still(0.3, 10) + right(0.3) + still(0.6, 10) + [None] * 3 + still(0.3, 10) + right(0.3) + still(0.6, 10)
        self.assertEqual(self.run_track(track), ["Swipe right", "Swipe right"])

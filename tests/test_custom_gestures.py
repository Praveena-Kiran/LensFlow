"""
Tests for custom gesture normalisation, matching, storage and recording checks.

Run from the repo root:
    python -m unittest discover tests
"""

import math
import os
import random
import tempfile
import unittest

from backend.gestures.custom_gestures import (
    CustomGestureMatcher,
    CustomGestureStore,
    MAX_SAMPLES_PER_GESTURE,
    normalize_landmarks,
    pose_distance,
    review_recording,
)


def make_hand(seed):
    """A random but fixed 21-point 'hand' with a non-degenerate palm."""

    rng = random.Random(seed)
    points = [(0.0, 0.0, 0.0)]

    for i in range(1, 21):
        points.append((
            rng.uniform(-0.08, 0.08),
            rng.uniform(-0.10, 0.0),
            rng.uniform(-0.03, 0.03),
        ))

    points[9] = (0.01, -0.09, 0.0)
    return points


def transform(points, dx=0.0, dy=0.0, dz=0.0, scale=1.0, mirror=False):
    out = []
    for x, y, z in points:
        x = -x if mirror else x
        out.append((x * scale + dx, y * scale + dy, z * scale + dz))
    return out


def jitter(points, amount, seed):
    rng = random.Random(seed)
    return [
        (x + rng.gauss(0, amount), y + rng.gauss(0, amount), z + rng.gauss(0, amount))
        for x, y, z in points
    ]


class NormalizeTests(unittest.TestCase):

    def test_invariant_to_position_and_size(self):
        hand = make_hand(1)
        a = normalize_landmarks(hand)
        b = normalize_landmarks(transform(hand, dx=0.3, dy=-0.2, dz=0.1, scale=1.7))
        self.assertAlmostEqual(pose_distance(a, b), 0.0, places=6)

    def test_left_hand_is_mirrored_onto_right(self):
        hand = make_hand(2)
        right = normalize_landmarks(hand, "Right")
        left = normalize_landmarks(transform(hand, mirror=True), "Left")
        self.assertAlmostEqual(pose_distance(right, left), 0.0, places=6)

    def test_palm_length_is_one(self):
        v = normalize_landmarks(make_hand(3))
        self.assertAlmostEqual(math.sqrt(sum(c * c for c in v[27:30])), 1.0, places=6)

    def test_rejects_bad_input(self):
        self.assertIsNone(normalize_landmarks(None))
        self.assertIsNone(normalize_landmarks([(0, 0, 0)] * 5))
        self.assertIsNone(normalize_landmarks([(0, 0, 0)] * 21))  # zero palm size

    def test_accepts_mediapipe_style_objects(self):
        class LM:
            def __init__(self, x, y, z):
                self.x, self.y, self.z = x, y, z

        hand = make_hand(4)
        self.assertEqual(
            normalize_landmarks([LM(*p) for p in hand]),
            normalize_landmarks(hand),
        )


def samples_for(hand, n=20, noise=0.002, seed=0):
    return [normalize_landmarks(jitter(hand, noise, seed + i)) for i in range(n)]


class MatcherTests(unittest.TestCase):

    def setUp(self):
        self.hand_a = make_hand(10)
        self.hand_b = make_hand(20)
        self.matcher = CustomGestureMatcher([
            {"name": "A", "samples": samples_for(self.hand_a)},
            {"name": "B", "samples": samples_for(self.hand_b)},
        ])

    def test_matches_recorded_pose_anywhere_on_screen(self):
        live = transform(jitter(self.hand_a, 0.002, 999), dx=0.2, scale=0.6)
        name, confidence = self.matcher.match(live)
        self.assertEqual(name, "A")
        self.assertGreaterEqual(confidence, 0.6)
        self.assertLessEqual(confidence, 1.0)

    def test_matches_other_hand(self):
        live = transform(self.hand_b, mirror=True)
        self.assertEqual(self.matcher.match(live, "Left")[0], "B")

    def test_rejects_unknown_pose(self):
        self.assertEqual(self.matcher.match(make_hand(30)), (None, 0.0))

    def test_rejects_ambiguous_pose_between_two_gestures(self):
        a = normalize_landmarks(self.hand_a)
        matcher = CustomGestureMatcher(
            [
                {"name": "A", "samples": [a]},
                {"name": "A2", "samples": [[v + 0.001 for v in a]]},
            ],
        )
        self.assertEqual(matcher.match_vector(a), (None, 0.0))

    def test_no_gestures_means_no_match(self):
        self.assertFalse(CustomGestureMatcher([]).has_gestures())
        self.assertEqual(CustomGestureMatcher([]).match(self.hand_a), (None, 0.0))
        self.assertEqual(self.matcher.match(None), (None, 0.0))


class StoreTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "custom_gestures.json")

    def tearDown(self):
        self.tmp.cleanup()

    def test_round_trip_replace_and_delete(self):
        store = CustomGestureStore(self.path)
        self.assertEqual(store.names(), [])

        store.add("Wave", samples_for(make_hand(1), n=5))
        store.add("Wave", samples_for(make_hand(2), n=7))  # replaces
        store.add("Pinch", samples_for(make_hand(3), n=5))

        reloaded = CustomGestureStore(self.path)
        self.assertEqual(sorted(reloaded.names()), ["Pinch", "Wave"])
        self.assertEqual(len(reloaded.get("Wave")["samples"]), 7)

        self.assertTrue(reloaded.delete("Wave"))
        self.assertFalse(reloaded.delete("Wave"))
        self.assertEqual(CustomGestureStore(self.path).names(), ["Pinch"])

    def test_limits_samples(self):
        store = CustomGestureStore(self.path)
        entry = store.add("Many", samples_for(make_hand(1), n=200))
        self.assertEqual(len(entry["samples"]), MAX_SAMPLES_PER_GESTURE)

    def test_corrupt_file_is_treated_as_empty(self):
        with open(self.path, "w") as f:
            f.write("{not json")
        self.assertEqual(CustomGestureStore(self.path).names(), [])


class ReviewRecordingTests(unittest.TestCase):

    BUILTINS = ["👍 Thumbs Up"]

    def review(self, name="Pinch", samples=None, builtin_hits=0, existing=()):
        if samples is None:
            samples = samples_for(make_hand(40), n=30)
        return review_recording(name, samples, builtin_hits, list(existing), self.BUILTINS)

    def test_good_recording(self):
        self.assertTrue(self.review()[0])

    def test_needs_name(self):
        self.assertFalse(self.review(name="  ")[0])

    def test_rejects_builtin_name(self):
        self.assertFalse(self.review(name="👍 Thumbs Up")[0])

    def test_rejects_too_few_frames(self):
        self.assertFalse(self.review(samples=samples_for(make_hand(40), n=5))[0])

    def test_rejects_pose_that_looks_builtin(self):
        self.assertFalse(self.review(builtin_hits=25)[0])

    def test_rejects_pose_too_close_to_existing_custom_gesture(self):
        hand = make_hand(50)
        existing = [{"name": "Old", "samples": samples_for(hand, seed=100)}]
        ok, message = self.review(samples=samples_for(hand, n=30), existing=existing)
        self.assertFalse(ok)
        self.assertIn("Old", message)

    def test_rerecording_same_name_is_allowed(self):
        hand = make_hand(50)
        existing = [{"name": "Pinch", "samples": samples_for(hand, seed=100)}]
        self.assertTrue(self.review(samples=samples_for(hand, n=30), existing=existing)[0])


if __name__ == "__main__":
    unittest.main()

"""
Custom gestures: let each user teach LensFlow their own hand poses.

Why this exists
---------------
MediaPipe only knows six fixed gestures. Some people can't comfortably make
those shapes, so LensFlow lets a user record *any* pose they can hold and
map it to an action. Recognition is template matching on hand landmarks:

1. MediaPipe gives 21 3D landmarks per hand (we use the "world" landmarks,
   which are in real-world units and don't depend on the image's aspect ratio).
2. normalize_landmarks() makes a pose comparable no matter where the hand is,
   how big it looks or which hand is used:
     - translate so the wrist (landmark 0) is the origin,
     - scale so the wrist -> middle-finger knuckle (landmark 9) distance is 1,
     - mirror left hands onto right hands.
3. CustomGestureMatcher compares a live pose against every recorded sample
   (nearest neighbour). A match is accepted only if it is
     - close enough:   distance <= max_distance, and
     - unambiguous:    the next-closest *different* gesture is at least
                       min_margin further away.
   The margin is what stops a pose halfway between two gestures from
   triggering either of them.

Data is stored in the user's data folder as custom_gestures.json.
"""

import json
import math
import time

from backend.paths import user_config_path


NUM_LANDMARKS = 21

WRIST = 0
MIDDLE_MCP = 9

# Default thresholds, in units of "palm length" (wrist -> middle knuckle).
# Measured on MediaPipe's sample photos: the same pose resized, shifted,
# tilted 10 degrees or made with the other hand stays within ~0.22, while
# different poses were 0.75-1.7 apart. 0.35 tolerates natural wobble and
# still leaves a wide gap before a different gesture could match.
DEFAULT_MAX_DISTANCE = 0.35
DEFAULT_MIN_MARGIN = 0.05

# Accepted matches are reported with a confidence in [0.6, 1.0] so they pass
# the GestureStabilizer's default 0.60 threshold; 1.0 means a perfect match.
MIN_MATCH_CONFIDENCE = 0.6

MAX_SAMPLES_PER_GESTURE = 60

STORE_VERSION = 1


# =========================================================
# NORMALISATION
# =========================================================

def normalize_landmarks(landmarks, handedness=None):
    """
    Turn 21 (x, y, z) landmarks into a flat list of 63 floats that is
    independent of hand position, hand size and left/right hand.

    `landmarks` may be MediaPipe landmark objects or (x, y, z) tuples.
    Returns None if the input is unusable.
    """

    if landmarks is None or len(landmarks) != NUM_LANDMARKS:
        return None

    points = []

    for lm in landmarks:

        if hasattr(lm, "x"):
            points.append((lm.x, lm.y, lm.z))
        else:
            points.append((lm[0], lm[1], lm[2]))

    wx, wy, wz = points[WRIST]

    points = [
        (x - wx, y - wy, z - wz)
        for x, y, z in points
    ]

    scale = math.sqrt(sum(c * c for c in points[MIDDLE_MCP]))

    if scale < 1e-6:
        return None

    mirror = -1.0 if handedness == "Left" else 1.0

    vector = []

    for x, y, z in points:
        vector.extend((
            mirror * x / scale,
            y / scale,
            z / scale,
        ))

    return vector


def pose_distance(a, b):
    """Mean distance between corresponding landmarks of two normalised poses."""

    total = 0.0

    for i in range(0, len(a), 3):
        dx = a[i] - b[i]
        dy = a[i + 1] - b[i + 1]
        dz = a[i + 2] - b[i + 2]
        total += math.sqrt(dx * dx + dy * dy + dz * dz)

    return total / (len(a) // 3)


# =========================================================
# STORAGE
# =========================================================

class CustomGestureStore:
    """Loads and saves the user's custom gestures."""

    def __init__(self, path=None):

        self.path = path or user_config_path("custom_gestures.json")
        self.gestures = []
        self.load()

    def load(self):

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}

        self.gestures = [
            g for g in data.get("gestures", [])
            if g.get("name") and g.get("samples")
        ]

    def save(self):

        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "version": STORE_VERSION,
                    "gestures": self.gestures,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

    def names(self):
        return [g["name"] for g in self.gestures]

    def get(self, name):

        for g in self.gestures:
            if g["name"] == name:
                return g

        return None

    def add(self, name, samples):
        """Add (or replace) a gesture. `samples` are normalised vectors."""

        samples = _downsample(samples, MAX_SAMPLES_PER_GESTURE)

        entry = {
            "name": name,
            "samples": [
                [round(v, 4) for v in s]
                for s in samples
            ],
            "created": time.strftime("%Y-%m-%d"),
        }

        self.gestures = [g for g in self.gestures if g["name"] != name]
        self.gestures.append(entry)
        self.save()

        return entry

    def delete(self, name):

        before = len(self.gestures)
        self.gestures = [g for g in self.gestures if g["name"] != name]

        if len(self.gestures) != before:
            self.save()
            return True

        return False


def _downsample(samples, limit):
    """Keep at most `limit` samples, spread evenly across the recording."""

    if len(samples) <= limit:
        return list(samples)

    step = len(samples) / limit
    return [samples[int(i * step)] for i in range(limit)]


# =========================================================
# MATCHING
# =========================================================

class CustomGestureMatcher:

    def __init__(
        self,
        gestures=None,
        max_distance=DEFAULT_MAX_DISTANCE,
        min_margin=DEFAULT_MIN_MARGIN,
    ):

        self.max_distance = max_distance
        self.min_margin = min_margin
        self.gestures = []

        if gestures is not None:
            self.set_gestures(gestures)

    @classmethod
    def from_store(cls, store=None, **kwargs):
        store = store or CustomGestureStore()
        return cls(store.gestures, **kwargs)

    def set_gestures(self, gestures):
        self.gestures = [
            (g["name"], g["samples"])
            for g in gestures
            if g.get("samples")
        ]

    def has_gestures(self):
        return bool(self.gestures)

    def closest(self, vector):
        """
        Return [(name, best_distance), ...] for every gesture, closest first.
        """

        results = []

        for name, samples in self.gestures:
            best = min(pose_distance(vector, s) for s in samples)
            results.append((name, best))

        results.sort(key=lambda item: item[1])
        return results

    def match_vector(self, vector):
        """Match an already-normalised pose. Returns (name, confidence) or (None, 0.0)."""

        if vector is None or not self.gestures:
            return None, 0.0

        ranked = self.closest(vector)
        name, distance = ranked[0]

        if distance > self.max_distance:
            return None, 0.0

        if len(ranked) > 1 and ranked[1][1] - distance < self.min_margin:
            return None, 0.0

        confidence = 1.0 - (1.0 - MIN_MATCH_CONFIDENCE) * (
            distance / self.max_distance
        )

        return name, confidence

    def match(self, landmarks, handedness=None):
        """Match raw landmarks. Returns (name, confidence) or (None, 0.0)."""

        return self.match_vector(
            normalize_landmarks(landmarks, handedness)
        )


# =========================================================
# RECORDING CHECKS
# =========================================================

def review_recording(
    name,
    samples,
    builtin_hits,
    existing_gestures,
    builtin_names,
    min_samples=15,
    max_builtin_ratio=0.5,
    max_distance=DEFAULT_MAX_DISTANCE,
):
    """
    Decide whether a new recording can be saved.

    samples          -- normalised vectors captured while recording
    builtin_hits     -- how many of those frames MediaPipe confidently
                        classified as one of its built-in gestures
    existing_gestures -- the store's current gestures (to detect clashes)
    builtin_names    -- display names of the built-in gestures

    Returns (ok, message).
    """

    name = (name or "").strip()

    if not name:
        return False, "Give your gesture a name."

    if name in builtin_names:
        return False, f'"{name}" is a built-in gesture name. Pick another name.'

    if len(samples) < min_samples:
        return False, (
            "Not enough of your hand was seen. Keep your whole hand in "
            "view of the camera and try again."
        )

    if builtin_hits / len(samples) > max_builtin_ratio:
        return False, (
            "This pose looks like one of LensFlow's built-in gestures, so "
            "it could trigger the wrong action. Try a different pose."
        )

    others = [g for g in existing_gestures if g["name"] != name]

    if others:

        matcher = CustomGestureMatcher(others, max_distance=max_distance)
        clashes = {}

        for vector in samples:
            ranked = matcher.closest(vector)
            if ranked and ranked[0][1] <= max_distance:
                clashes[ranked[0][0]] = clashes.get(ranked[0][0], 0) + 1

        if clashes:
            other, count = max(clashes.items(), key=lambda item: item[1])
            if count / len(samples) > 0.3:
                return False, (
                    f'This pose is too similar to your "{other}" gesture. '
                    "Try a more distinct pose."
                )

    return True, "Looks good."

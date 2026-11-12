"""
Motion gestures: swipes, waves, circles — anything the hand *draws*.

Pipeline
--------
1. palm_point() gives the palm centre in screen-proportional coordinates
   (x scaled by the frame's aspect ratio so left/right and up/down movements
   are measured in the same units), plus the palm size in those units.
2. MotionSegmenter watches the palm over time. A stroke starts when the
   hand moves faster than `start_speed` (palm-lengths per second) and ends
   once it has been slower than `stop_speed` for `settle_time`, or the hand
   disappears. Too short / too small strokes are ignored.
3. normalize_trajectory() makes a stroke comparable to others:
   start at the origin, total path length 1 (big and small swipes match),
   resampled to N points evenly spaced along the path (fast and slow match).
4. MotionMatcher compares a stroke to recorded templates with dynamic time
   warping (DTW), which tolerates parts of the motion being done at
   different speeds. As with poses, a match must be close enough AND
   clearly closer than any other motion.

Built-in motions (swipes in four directions) are generated, so they work
without recording anything. Users' own motions live in custom_motions.json.
"""

import json
import math
import time

from backend.paths import user_config_path


RESAMPLE_POINTS = 32

# DTW limits for the user's own motions (trajectory length = 1).
DEFAULT_MAX_DISTANCE = 0.10
DEFAULT_MIN_MARGIN = 0.02

# Built-in swipes are recognised by shape rules instead of DTW: plain DTW
# can't tell "a swipe drawn 20 degrees off" from "an L-shape" (both ~0.09).
# Measured: swipes (tilted/curved/noisy) have straightness 0.88-0.95, waves,
# L-shapes and circles 0.71 or less.
SWIPE_MIN_STRAIGHTNESS = 0.8
SWIPE_MAX_ANGLE = 30  # degrees either side of left/right/up/down
MIN_MATCH_CONFIDENCE = 0.6

PALM_POINTS = (0, 5, 9, 13, 17)  # wrist + finger bases

STORE_VERSION = 1


# =========================================================
# PALM TRACKING
# =========================================================

def palm_point(image_landmarks, aspect=4 / 3):
    """
    (x, y, palm_size) for MediaPipe image landmarks, or None.
    x is multiplied by the frame aspect (width / height) so both axes use
    the same unit. y grows downwards, as on screen.
    """

    if image_landmarks is None or len(image_landmarks) < 21:
        return None

    def xy(i):
        lm = image_landmarks[i]
        x, y = (lm.x, lm.y) if hasattr(lm, "x") else (lm[0], lm[1])
        return x * aspect, y

    pts = [xy(i) for i in PALM_POINTS]
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)

    wx, wy = xy(0)
    mx, my = xy(9)
    size = math.hypot(mx - wx, my - wy)

    if size < 1e-6:
        return None

    return cx, cy, size


# Which point of the hand a motion follows.
PALM = "palm"            # whole-hand movements (swipes, waves)
FINGERTIP = "fingertip"  # things drawn with the index finger (a circle, a "0")

INDEX_TIP = 8

# A take counts as "drawn with the finger" when the fingertip travelled at
# least this many times further than the palm.
FINGERTIP_TRAVEL_RATIO = 1.5


def fingertip_point(image_landmarks, aspect=4 / 3):
    """
    (x, y, palm_size) of the index fingertip, in the same units as
    palm_point(). Speeds and sizes are still measured in palm lengths, so
    the same segmenter settings work for both.
    """

    palm = palm_point(image_landmarks, aspect)

    if palm is None:
        return None

    lm = image_landmarks[INDEX_TIP]
    x, y = (lm.x, lm.y) if hasattr(lm, "x") else (lm[0], lm[1])
    return x * aspect, y, palm[2]


def hand_points(image_landmarks, aspect=4 / 3):
    """{"palm": sample, "fingertip": sample} for one frame (values may be None)."""
    return {
        PALM: palm_point(image_landmarks, aspect),
        FINGERTIP: fingertip_point(image_landmarks, aspect),
    }


def motion_point(motion):
    """The point a stored motion follows (older recordings: the palm)."""
    return motion.get("point") or PALM


def choose_point(fingertip_points, palm_points):
    """FINGERTIP if the finger moved much further than the palm, else PALM."""
    tip = path_length(fingertip_points or [])
    palm = path_length(palm_points or [])
    if tip > 0 and (palm < 1e-9 or tip / palm >= FINGERTIP_TRAVEL_RATIO):
        return FINGERTIP
    return PALM


class MotionSegmenter:
    """Cuts the stream of palm positions into individual strokes."""

    def __init__(
        self,
        start_speed=1.8,      # palm-lengths / second to start a stroke
        stop_speed=0.8,       # ... and below this to end it
        settle_time=0.12,     # seconds slow before the stroke ends
        min_duration=0.15,
        max_duration=2.0,
        min_travel=1.2,       # palm-lengths of total movement
    ):
        self.start_speed = start_speed
        self.stop_speed = stop_speed
        self.settle_time = settle_time
        self.min_duration = min_duration
        self.max_duration = max_duration
        self.min_travel = min_travel

        self.reset()

    def reset(self):
        # Why the last started stroke was thrown away (for the log), or None.
        self.dropped = None
        self.last = None          # (t, x, y)
        self.stroke = []          # [(t, x, y)]
        self.scales = []
        self.slow_since = None

    @property
    def active(self):
        """True while a stroke is being drawn (poses should be ignored)."""
        return bool(self.stroke)

    def update(self, t, sample):
        """
        Feed one frame: `sample` is palm_point()'s (x, y, size) or None.
        Returns a finished stroke {"points": [(x, y)...], "scale": s} or None.
        """

        if sample is None:
            finished = self._finish()
            self.last = None
            return finished

        x, y, size = sample

        if self.last is None:
            self.last = (t, x, y)
            return None

        lt, lx, ly = self.last
        dt = max(t - lt, 1e-3)
        speed = math.hypot(x - lx, y - ly) / size / dt
        self.last = (t, x, y)

        if not self.stroke:

            if speed >= self.start_speed:
                self.stroke = [(lt, lx, ly), (t, x, y)]
                self.scales = [size]
                self.slow_since = None

            return None

        self.stroke.append((t, x, y))
        self.scales.append(size)

        if t - self.stroke[0][0] > self.max_duration:
            # Hand kept moving: not a gesture stroke.
            self.reset()
            self.dropped = (
                f"hand kept moving for over {self.max_duration:g} s "
                "(pause briefly after the movement)"
            )
            self.last = (t, x, y)
            return None

        if speed < self.stop_speed:
            if self.slow_since is None:
                self.slow_since = t
            elif t - self.slow_since >= self.settle_time:
                return self._finish()
        else:
            self.slow_since = None

        return None

    def _finish(self):

        stroke, scales = self.stroke, self.scales
        self.stroke, self.scales, self.slow_since = [], [], None

        if not stroke:
            return None

        if len(stroke) < 3:
            self.dropped = f"too few camera frames ({len(stroke)})"
            return None

        duration = stroke[-1][0] - stroke[0][0]

        if duration < self.min_duration:
            self.dropped = (
                f"too quick ({duration:.2f} s, need {self.min_duration:g} s)"
            )
            return None

        scale = sum(scales) / len(scales)
        points = [(x, y) for _, x, y in stroke]

        travel = path_length(points) / scale
        if travel < self.min_travel:
            self.dropped = (
                f"too small ({travel:.1f} hand-lengths, need {self.min_travel:g})"
            )
            return None

        return {
            "points": points,
            "scale": scale,
            "duration": duration,
            "t0": stroke[0][0],
            "t1": stroke[-1][0],
        }


# =========================================================
# NORMALISATION
# =========================================================

def path_length(points):
    return sum(
        math.hypot(b[0] - a[0], b[1] - a[1])
        for a, b in zip(points, points[1:])
    )


def resample(points, n=RESAMPLE_POINTS):
    """n points evenly spaced along the path (by distance, not time)."""

    total = path_length(points)

    if total < 1e-9:
        return [tuple(points[0])] * n

    # Cumulative distance at each input point.
    cumulative = [0.0]
    for a, b in zip(points, points[1:]):
        cumulative.append(cumulative[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))

    out = []
    seg = 1

    for k in range(n):
        target = total * k / (n - 1)

        while seg < len(points) - 1 and cumulative[seg] < target:
            seg += 1

        d0, d1 = cumulative[seg - 1], cumulative[seg]
        a, b = points[seg - 1], points[seg]
        r = 0.0 if d1 - d0 < 1e-12 else (target - d0) / (d1 - d0)
        out.append((a[0] + r * (b[0] - a[0]), a[1] + r * (b[1] - a[1])))

    return out


def normalize_trajectory(points):
    """Origin at the start, total length 1, RESAMPLE_POINTS points. Flat list."""

    if not points or len(points) < 2:
        return None

    total = path_length(points)

    if total < 1e-9:
        return None

    x0, y0 = points[0]
    scaled = [((x - x0) / total, (y - y0) / total) for x, y in points]

    flat = []
    for x, y in resample(scaled):
        flat.extend((x, y))

    return flat


def dtw_distance(a, b, window=6):
    """
    Dynamic time warping distance between two normalised trajectories
    (flat [x0, y0, x1, y1, ...] lists of equal length), averaged per point.
    `window` limits how far the alignment may drift (Sakoe-Chiba band).
    """

    n = len(a) // 2
    m = len(b) // 2
    inf = float("inf")

    cost = [[inf] * (m + 1) for _ in range(n + 1)]
    cost[0][0] = 0.0

    for i in range(1, n + 1):
        ax, ay = a[2 * i - 2], a[2 * i - 1]
        lo = max(1, i - window)
        hi = min(m, i + window)
        for j in range(lo, hi + 1):
            d = math.hypot(ax - b[2 * j - 2], ay - b[2 * j - 1])
            cost[i][j] = d + min(cost[i - 1][j], cost[i][j - 1], cost[i - 1][j - 1])

    return cost[n][m] / (n + m)


# =========================================================
# BUILT-IN MOTIONS (swipes)
# =========================================================

SWIPE_DIRECTIONS = {
    "Swipe right": 0,
    "Swipe down": 90,     # screen y grows downwards
    "Swipe left": 180,
    "Swipe up": 270,
}

BUILTIN_MOTION_NAMES = list(SWIPE_DIRECTIONS)


def ideal_swipe(name):
    """A perfectly straight swipe as a normalised trajectory."""
    angle = math.radians(SWIPE_DIRECTIONS[name])
    return normalize_trajectory([(0.0, 0.0), (math.cos(angle), math.sin(angle))])


def straightness(trajectory):
    """Start-to-end distance / path length (1 = perfectly straight)."""
    # A normalised trajectory starts at 0,0 and has path length 1.
    return math.hypot(trajectory[-2], trajectory[-1])


def classify_swipe(
    trajectory,
    min_straightness=SWIPE_MIN_STRAIGHTNESS,
    max_angle=SWIPE_MAX_ANGLE,
):
    """(swipe name, confidence) for a normalised trajectory, or (None, 0.0)."""

    if trajectory is None:
        return None, 0.0

    s = straightness(trajectory)

    if s < min_straightness:
        return None, 0.0

    angle = math.degrees(math.atan2(trajectory[-1], trajectory[-2])) % 360

    for name, direction in SWIPE_DIRECTIONS.items():
        off = abs((angle - direction + 180) % 360 - 180)
        if off <= max_angle:
            confidence = MIN_MATCH_CONFIDENCE + (1 - MIN_MATCH_CONFIDENCE) * min(
                (s - min_straightness) / max(1 - min_straightness, 1e-6),
                1 - off / max_angle,
            )
            return name, confidence

    return None, 0.0


# =========================================================
# STORAGE
# =========================================================

class MotionStore:
    """The user's recorded motions (custom_motions.json)."""

    def __init__(self, path=None):
        self.path = path or user_config_path("custom_motions.json")
        self.motions = []
        self.load()

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}

        self.motions = [
            m for m in data.get("motions", [])
            if m.get("name") and m.get("samples")
        ]

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(
                {"version": STORE_VERSION, "motions": self.motions},
                f, indent=2, ensure_ascii=False,
            )

    def names(self):
        return [m["name"] for m in self.motions]

    def get(self, name):
        return next((m for m in self.motions if m["name"] == name), None)

    def add(self, name, samples, point=PALM):
        entry = {
            "name": name,
            "samples": [[round(v, 4) for v in s] for s in samples],
            "point": point,
            "created": time.strftime("%Y-%m-%d"),
        }
        self.motions = [m for m in self.motions if m["name"] != name]
        self.motions.append(entry)
        self.save()
        return entry

    def delete(self, name):
        before = len(self.motions)
        self.motions = [m for m in self.motions if m["name"] != name]
        if len(self.motions) != before:
            self.save()
            return True
        return False


# =========================================================
# MATCHING
# =========================================================

class MotionMatcher:

    def __init__(
        self,
        motions=None,
        include_builtin=True,
        max_distance=DEFAULT_MAX_DISTANCE,
        min_margin=DEFAULT_MIN_MARGIN,
        swipe_min_straightness=SWIPE_MIN_STRAIGHTNESS,
        swipe_max_angle=SWIPE_MAX_ANGLE,
        point=None,
    ):
        """`point`: only use recordings that follow this point (PALM or
        FINGERTIP); None uses all of them."""
        self.max_distance = max_distance
        self.min_margin = min_margin
        self.include_builtin = include_builtin
        self.swipe_min_straightness = swipe_min_straightness
        self.swipe_max_angle = swipe_max_angle

        self.templates = []

        for m in motions or []:
            if point is not None and motion_point(m) != point:
                continue
            # Ignore takes that are really straight swipes: one such take
            # inside a recording made every near-straight movement match
            # it (recordings saved before review_motion checked each take
            # can contain one).
            samples = [
                sample for sample in m.get("samples") or []
                if not classify_swipe(sample)[0]
            ]
            if samples:
                self.templates.append((m["name"], samples))

    @classmethod
    def from_store(cls, store=None, **kwargs):
        store = store or MotionStore()
        return cls(store.motions, **kwargs)

    def closest(self, trajectory):
        ranked = [
            (name, min(dtw_distance(trajectory, s) for s in samples))
            for name, samples in self.templates
        ]
        ranked.sort(key=lambda item: item[1])
        return ranked

    def match_custom(self, trajectory):
        """
        (name, confidence, distance) of the user's closest recorded motion
        if it is close enough and clearly closer than any other, otherwise
        (None, 0.0, distance-or-None).
        """

        if trajectory is None or not self.templates:
            return None, 0.0, None

        ranked = self.closest(trajectory)
        name, distance = ranked[0]

        if distance > self.max_distance:
            return None, 0.0, distance

        if len(ranked) > 1 and ranked[1][1] - distance < self.min_margin:
            return None, 0.0, distance

        confidence = 1.0 - (1.0 - MIN_MATCH_CONFIDENCE) * (distance / self.max_distance)
        return name, confidence, distance

    def match_trajectory(self, trajectory):
        """(name, confidence) or (None, 0.0) for a normalised trajectory."""

        if trajectory is None:
            return None, 0.0

        custom, custom_confidence, custom_distance = self.match_custom(trajectory)

        swipe, swipe_confidence = (None, 0.0)
        if self.include_builtin:
            swipe, swipe_confidence = classify_swipe(
                trajectory,
                self.swipe_min_straightness,
                self.swipe_max_angle,
            )

        if custom and swipe:
            # Could be either: a gently curved recorded motion can come out
            # straight enough to pass as a swipe, and a real swipe can be
            # near a recording. Pick whichever it is closer to: the user's
            # recording, or a perfectly straight swipe in that direction.
            # (Checking swipes first used to hide the user's motion, and
            # could even run the opposite action, e.g. "Swipe left".)
            if custom_distance < dtw_distance(trajectory, ideal_swipe(swipe)):
                return custom, custom_confidence
            return swipe, swipe_confidence

        if custom:
            return custom, custom_confidence

        if swipe:
            return swipe, swipe_confidence

        return None, 0.0

    def explain(self, trajectory):
        """One log line describing how a stroke was judged."""

        if trajectory is None:
            return "stroke too short"

        name, confidence = self.match_trajectory(trajectory)
        swipe, _ = classify_swipe(
            trajectory, self.swipe_min_straightness, self.swipe_max_angle
        )

        parts = [
            f"-> {name} ({confidence:.2f})" if name else "-> no match",
            f"straightness {straightness(trajectory):.2f}",
            f"looks like {swipe}" if swipe else "not a swipe",
        ]

        if self.templates:
            closest_name, closest = self.closest(trajectory)[0]
            parts.append(
                f'closest recording "{closest_name}" distance {closest:.3f} '
                f"(limit {self.max_distance:.3f})"
            )

        return ", ".join(parts)

    def match_stroke(self, stroke):
        """Match MotionSegmenter output."""
        if not stroke:
            return None, 0.0
        return self.match_trajectory(normalize_trajectory(stroke["points"]))


def review_motion(name, samples, existing_motions, taken_names, max_distance=DEFAULT_MAX_DISTANCE):
    """
    Check a recorded motion before saving. `samples` are normalised
    trajectories (one per take); `taken_names` are names used by built-in
    gestures/motions and the user's poses. Returns (ok, message).
    """

    name = (name or "").strip()

    if not name:
        return False, "Give your motion a name."

    if name in taken_names or name in BUILTIN_MOTION_NAMES:
        return False, f'"{name}" is already used. Pick another name.'

    if len(samples) < 2:
        return False, "Record at least two takes."

    # A take that came out as a straight swipe is ignored when matching
    # (see MotionMatcher), so judge the motion by its curved takes.
    swipe_like = [classify_swipe(s)[0] for s in samples]
    curved = [s for s, swipe in zip(samples, swipe_like) if not swipe]

    if not curved:
        return False, (
            f"This movement looks like a {swipe_like[0].lower()}, "
            "which is built in. Use that, or try a curvier movement."
        )

    if len(curved) < 2:
        return False, (
            "Most takes came out as straight swipes. Record again, making "
            "the same curved movement each time."
        )

    # Takes should agree with each other, or recognition will be unreliable.
    worst = max(
        dtw_distance(a, b)
        for i, a in enumerate(curved)
        for b in curved[i + 1:]
    )

    if worst > max_distance * 1.5:
        return False, (
            "Your takes were quite different from each other. Try to make "
            "the same movement each time."
        )

    samples = curved

    others = MotionMatcher(
        [m for m in existing_motions if m["name"] != name],
        include_builtin=True,
        max_distance=max_distance,
    )

    clashes = [others.match_trajectory(s)[0] for s in samples]
    clashes = [c for c in clashes if c]

    if len(clashes) > len(samples) / 2:
        return False, (
            f'This movement looks like "{clashes[0]}". Try something more '
            "distinct."
        )

    return True, "Looks good."


# =========================================================
# LIVE RECOGNITION
# =========================================================

OPPOSITE_SWIPES = {
    "Swipe left": "Swipe right",
    "Swipe right": "Swipe left",
    "Swipe up": "Swipe down",
    "Swipe down": "Swipe up",
}


class MotionRecognizer:
    """
    Segmenter + matcher for a live camera feed, plus one rule people expect:
    after a swipe you bring your hand back, which is itself a quick swipe the
    other way. A swipe in the opposite direction within `return_window`
    seconds is treated as that return movement and ignored.
    """

    def __init__(self, matcher=None, segmenter=None, return_window=0.7, label=""):
        self.label = f"{label}: " if label else ""
        self.matcher = matcher or MotionMatcher.from_store()
        self.segmenter = segmenter or MotionSegmenter()
        self.return_window = return_window
        self._last_swipe = None   # (name, end time)

    @property
    def active(self):
        return self.segmenter.active

    def update(self, t, sample):
        """Feed one frame. Returns (motion name, confidence) or None."""

        stroke = self.segmenter.update(t, sample)

        if not stroke:
            if self.segmenter.dropped:
                print(f"[motion] {self.label}movement ignored: {self.segmenter.dropped}")
                self.segmenter.dropped = None
            return None

        name, confidence = self.matcher.match_stroke(stroke)

        # One line per finished movement, so the log shows why a motion
        # did or didn't count (look for "[motion]" in wield.log).
        print(
            f"[motion] {self.label}{stroke.get('duration', 0):.2f} s "
            + self.matcher.explain(normalize_trajectory(stroke["points"]))
        )

        if not name:
            return None

        if name in OPPOSITE_SWIPES and self._last_swipe:
            last_name, last_t = self._last_swipe
            if (
                OPPOSITE_SWIPES[name] == last_name
                and t - last_t <= self.return_window
            ):
                self._last_swipe = None
                return None

        self._last_swipe = (name, t) if name in OPPOSITE_SWIPES else None

        return name, confidence


class HandMotionRecognizer:
    """
    Follows two points of the hand at once:
    - the palm: built-in swipes and recordings made by moving the whole hand;
    - the index fingertip: recordings drawn with a finger (a circle, a "0"),
      which barely move the palm.
    Feed it hand_points() for each frame.
    """

    def __init__(self, store=None, **matcher_kwargs):
        store = store or MotionStore()
        self.palm = MotionRecognizer(
            MotionMatcher(store.motions, point=PALM, **matcher_kwargs),
            label="palm",
        )
        # Fingertip strokes are only compared with fingertip recordings
        # (the swipes are judged by the palm).
        tip_kwargs = dict(matcher_kwargs, include_builtin=False)
        self.fingertip = MotionRecognizer(
            MotionMatcher(store.motions, point=FINGERTIP, **tip_kwargs),
            label="fingertip",
        )
        self.tracks_fingertip = bool(self.fingertip.matcher.templates)

    @property
    def active(self):
        return self.palm.active or (self.tracks_fingertip and self.fingertip.active)

    def update(self, t, points):
        """Feed one frame's hand_points(). Returns (name, confidence) or None."""
        points = points or {}
        result = None
        if self.tracks_fingertip:
            result = self.fingertip.update(t, points.get(FINGERTIP))
        palm_result = self.palm.update(t, points.get(PALM))
        return result or palm_result

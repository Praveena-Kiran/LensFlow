"""
Logic behind the foggy window on Home: which "pen" the hand is holding, and
where the saved note lives. The drawing itself is in
frontend/components/fog_window.py.

Hand modes (from MediaPipe image landmarks, no extra model):
    write  index finger out, the other three fingers curled -> wipes the fog
    pause  every finger curled (fist)                        -> moves freely
    wipe   every finger out (open palm)                      -> held, clears
    None   anything else / no hand
"""

import math
import os

from backend.paths import user_data_dir


NOTE_FILENAME = "fog_note.png"

WRIST = 0
FINGERS = {               # tip, middle joint (PIP)
    "index": (8, 6),
    "middle": (12, 10),
    "ring": (16, 14),
    "pinky": (20, 18),
}

# A finger is "out" when its tip is this much further from the wrist than
# its middle joint (as a fraction of the joint's distance).
EXTENDED_RATIO = 1.12


def _xy(lm):
    return (lm.x, lm.y) if hasattr(lm, "x") else (lm[0], lm[1])


def finger_states(landmarks):
    """{"index": True/False, ...} for 21 landmarks, or None."""

    if landmarks is None or len(landmarks) < 21:
        return None

    wx, wy = _xy(landmarks[WRIST])
    states = {}

    for name, (tip, pip) in FINGERS.items():
        tx, ty = _xy(landmarks[tip])
        px, py = _xy(landmarks[pip])
        tip_d = math.hypot(tx - wx, ty - wy)
        pip_d = math.hypot(px - wx, py - wy)
        states[name] = pip_d > 0 and tip_d > pip_d * EXTENDED_RATIO

    return states


def hand_mode(landmarks):
    """'write', 'pause', 'wipe' or None."""

    states = finger_states(landmarks)

    if states is None:
        return None

    others = [states["middle"], states["ring"], states["pinky"]]

    if states["index"] and not any(others):
        return "write"

    if not states["index"] and not any(others):
        return "pause"

    if states["index"] and all(others):
        return "wipe"

    return None


def fingertip(landmarks):
    """(x, y) of the index fingertip in 0..1 image coordinates, or None."""

    if landmarks is None or len(landmarks) < 21:
        return None

    return _xy(landmarks[8])


def note_path():
    return os.path.join(user_data_dir(), NOTE_FILENAME)

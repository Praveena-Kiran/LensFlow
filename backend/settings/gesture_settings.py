"""
Accessibility settings for gesture recognition.

Stored in the user's settings.json (via SettingsManager):

    sensitivity   0-100   how forgiving matching is (50 = the calibrated
                          defaults; higher accepts looser poses/motions,
                          useful with tremor or limited range of movement)
    hold_time     seconds a pose must be held before it triggers (0 = instant)
    require_arm   bool    gestures only work after an activation gesture
    arm_gesture   name    the activation gesture
    arm_timeout   seconds of no gestures before Wield deactivates again
    sound_feedback    bool  soft sounds when Wield activates / runs an action
    feedback_overlay  bool  small always-on-top note, visible over slideshows
    voice_enabled     bool  listen for spoken commands (offline)
    voice_wake_word   bool  commands must start with "Hey Wield"

thresholds() turns these into the numbers the matchers use.
"""

from backend.settings.settings_manager import SettingsManager


DEFAULTS = {
    "sensitivity": 50,
    "hold_time": 0.0,
    "require_arm": False,
    "arm_gesture": "✋ Open Palm",
    "arm_timeout": 10,
    "sound_feedback": True,
    "feedback_overlay": True,
    "voice_enabled": False,
    "voice_wake_word": True,
}

HOLD_TIME_CHOICES = [0.0, 0.3, 0.6, 1.0, 1.5]
ARM_TIMEOUT_CHOICES = [5, 10, 30, 60]


def load():
    """Current settings merged over the defaults."""

    try:
        stored = SettingsManager().settings
    except Exception:
        stored = {}

    values = dict(DEFAULTS)

    for key in DEFAULTS:
        if key in stored:
            values[key] = stored[key]

    values["sensitivity"] = max(0, min(100, int(values["sensitivity"])))
    values["hold_time"] = max(0.0, float(values["hold_time"]))
    values["arm_timeout"] = max(1, int(values["arm_timeout"]))
    for key in ("require_arm", "sound_feedback", "feedback_overlay",
                "voice_enabled", "voice_wake_word"):
        values[key] = bool(values[key])

    return values


def save(key, value):

    if key not in DEFAULTS:
        raise KeyError(key)

    SettingsManager().set_setting(key, value)


def thresholds(settings=None):
    """
    Matching thresholds for the current sensitivity. At 50 these equal the
    values calibrated on sample images; 0 is stricter, 100 more forgiving.
    """

    settings = settings or load()
    s = settings["sensitivity"] / 100.0

    return {
        # Custom poses: mean landmark distance in palm lengths.
        "pose_max_distance": 0.25 + 0.20 * s,          # 0.25 .. 0.45 (0.35)
        # Custom motions: DTW distance on unit-length trajectories.
        "motion_max_distance": 0.07 + 0.06 * s,        # 0.07 .. 0.13 (0.10)
        # Built-in swipes.
        "swipe_min_straightness": 0.85 - 0.10 * s,     # 0.85 .. 0.75 (0.80)
        "swipe_max_angle": 25 + 10 * s,                # 25 .. 35 deg (30)
        # Built-in MediaPipe gestures: minimum confidence.
        "min_confidence": 0.70 - 0.20 * s,             # 0.70 .. 0.50 (0.60)
        "hold_time": settings["hold_time"],
    }

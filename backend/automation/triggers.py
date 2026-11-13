"""
Triggers: the things that can run an action. A trigger is a hand
gesture (a pose), a motion (a movement), built in or recorded by the user,
or a spoken voice command ("🎤 next slide").

Profiles store {trigger: action}, so one action can have several triggers
(e.g. Next slide on both 👍 Thumbs Up and a recorded "forward" motion), and
a trigger can only belong to one action at a time.
"""

from backend.gestures.gesture_names import BUILTIN_GESTURE_NAMES
from backend.gestures.motions import BUILTIN_MOTION_NAMES
from backend.voice.commands import DEFAULT_PHRASES, is_voice_trigger, voice_trigger

GESTURE = "gesture"
MOTION = "motion"
CUSTOM_GESTURE = "custom gesture"
CUSTOM_MOTION = "custom motion"
VOICE = "voice"
MISSING = "missing"

# Labels for the kinds, as shown in the UI.
KIND_LABELS = {
    GESTURE: "Gesture",
    MOTION: "Motion",
    CUSTOM_GESTURE: "Your gesture",
    CUSTOM_MOTION: "Your motion",
    VOICE: "Voice",
    MISSING: "Deleted",
}


def trigger_kind(name, custom_gestures=(), custom_motions=()):
    if name in BUILTIN_GESTURE_NAMES:
        return GESTURE
    if name in BUILTIN_MOTION_NAMES:
        return MOTION
    if name in custom_gestures:
        return CUSTOM_GESTURE
    if name in custom_motions:
        return CUSTOM_MOTION
    if is_voice_trigger(name):
        return VOICE
    return MISSING


def is_motion(kind):
    return kind in (MOTION, CUSTOM_MOTION)


def catalogue(custom_gestures=(), custom_motions=(), voice_triggers=()):
    """
    Every trigger the user can pick, grouped: [(group title, [names])].
    `voice_triggers`: voice triggers already in use (custom phrases), shown
    with the built-in phrases.
    """
    voice = [voice_trigger(p) for p in DEFAULT_PHRASES]
    voice += [v for v in voice_triggers if is_voice_trigger(v) and v not in voice]
    groups = [
        ("Hand gestures", list(BUILTIN_GESTURE_NAMES)),
        ("Motions", list(BUILTIN_MOTION_NAMES)),
        ("Your gestures", list(custom_gestures)),
        ("Your motions", list(custom_motions)),
        ("Voice commands", voice),
    ]
    return [(title, names) for title, names in groups if names]


def triggers_by_action(gesture_map, actions):
    """{action: [triggers]} for `actions`, in the profile's order."""
    result = {action: [] for action in actions}
    for trigger, action in (gesture_map or {}).items():
        if action in result:
            result[action].append(trigger)
    return result

"""
The simple "one gesture + one phrase per action" view of a presentation
profile, used by Presentation Studio's controls.

A profile maps triggers to actions ({trigger: action}); an action can have
several triggers (set up in Gesture Studio). Here each action shows:
  - its main gesture or motion (the first non-voice trigger), and how many
    more it has;
  - its main voice phrase (the first voice trigger), and how many more.
Changing one replaces just that main trigger; the extras are kept.
"""

from backend.automation.events import friendly_action
from backend.voice.commands import (
    check_phrase,
    is_voice_trigger,
    normalize_phrase,
    phrase_of,
    voice_trigger,
)

ACTIONS = [
    "presentation_start",
    "presentation_next",
    "presentation_previous",
    "presentation_end",
]


def _triggers(gesture_map, action, voice):
    return [
        trigger for trigger, mapped in gesture_map.items()
        if mapped == action and is_voice_trigger(trigger) == voice
    ]


def binding(gesture_map, action):
    """
    {"gesture": str|None, "more_gestures": int,
     "phrase": str, "more_phrases": int}
    """
    gestures = _triggers(gesture_map, action, voice=False)
    phrases = _triggers(gesture_map, action, voice=True)
    return {
        "gesture": gestures[0] if gestures else None,
        "more_gestures": max(0, len(gestures) - 1),
        "phrase": phrase_of(phrases[0]) if phrases else "",
        "more_phrases": max(0, len(phrases) - 1),
    }


def set_gesture(gesture_map, action, gesture):
    """
    Make `gesture` the action's main gesture (None = no main gesture).
    Edits `gesture_map` in place. Returns a note for the user, e.g.
    "👍 Thumbs Up was on Previous slide; it's now on Next slide.", or "".
    """
    current = binding(gesture_map, action)["gesture"]

    if gesture == current:
        return ""

    note = ""
    if gesture is not None:
        previous = gesture_map.get(gesture)
        if previous and previous != action:
            note = (
                f"{gesture} was on {friendly_action(previous)}; "
                f"it's now on {friendly_action(action)}."
            )

    if current is not None:
        del gesture_map[current]

    if gesture is not None:
        gesture_map.pop(gesture, None)
        gesture_map[gesture] = action

    return note


def check_voice(gesture_map, action, phrase):
    """(ok, message) for typing `phrase` as the action's main voice phrase."""
    phrase = normalize_phrase(phrase)
    if not phrase:
        return True, ""

    current = binding(gesture_map, action)["phrase"]
    if phrase == current:
        return True, ""

    used = gesture_map.get(voice_trigger(phrase))
    if used:
        return False, f"“{phrase}” is already used for {friendly_action(used)}."

    # Other checks (length, wake phrase); duplicates were handled above.
    return check_phrase(phrase)


def set_voice(gesture_map, action, phrase):
    """
    Make `phrase` the action's main voice phrase ("" = no phrase).
    Edits `gesture_map` in place. Returns (ok, message); nothing changes
    when not ok.
    """
    ok, message = check_voice(gesture_map, action, phrase)
    if not ok:
        return False, message

    phrase = normalize_phrase(phrase)
    current = binding(gesture_map, action)["phrase"]

    if phrase == current:
        return True, ""

    if current:
        del gesture_map[voice_trigger(current)]

    if phrase:
        gesture_map[voice_trigger(phrase)] = action

    return True, ""

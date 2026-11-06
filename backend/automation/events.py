"""
One event model for every studio: a trigger plus an action.

    {
        "name":    "Next slide",
        "gesture": "👍 Thumbs Up",        # trigger (optional; "" = click only)
        "action":  "PowerPoint",          # what to do ...
        "value":   "next"                 # ... and with what
    }

Custom studios store events like this in studios.json. Built-in profiles
(backend/config/profiles/*.json) use an older {gesture: action_name} map;
profile_events() converts them so the gesture worker and the runner only
ever deal with events.

Triggers are read through trigger_of(), so new kinds (motions, schedules)
can be added in one place.
"""


# Actions an event can run (shown in the event editor).
ACTION_TYPES = [
    "Open Application",
    "Open File",
    "Open Website",
    "Hotkey",
    "PowerPoint",
    "Run Flow",
    "Wait",
]

# Example values, shown as placeholders in the event editor.
ACTION_HINTS = {
    "Open Application": "e.g. chrome, VS Code, or Browse to an .exe",
    "Open File": "Browse to a file",
    "Open Website": "e.g. https://github.com",
    "Hotkey": "e.g. ctrl+shift+t",
    "PowerPoint": "next, previous, start or end",
    "Run Flow": "Name of a flow in flows.json, e.g. coding_flow",
    "Wait": "Seconds, e.g. 2",
}

POWERPOINT_COMMANDS = {
    "next": "next_slide",
    "next slide": "next_slide",
    "next_slide": "next_slide",
    "previous": "previous_slide",
    "prev": "previous_slide",
    "previous slide": "previous_slide",
    "previous_slide": "previous_slide",
    "start": "start_presentation",
    "start presentation": "start_presentation",
    "start_presentation": "start_presentation",
    "end": "end_presentation",
    "stop": "end_presentation",
    "end presentation": "end_presentation",
    "end_presentation": "end_presentation",
}

# Built-in profile action names -> (event name, action, value)
PROFILE_ACTIONS = {
    "presentation_next": ("Next slide", "PowerPoint", "next"),
    "presentation_previous": ("Previous slide", "PowerPoint", "previous"),
    "presentation_start": ("Start presentation", "PowerPoint", "start"),
    "presentation_end": ("End presentation", "PowerPoint", "end"),
    # Arming LensFlow with a gesture; see the accessibility settings.
    "ACTIVATE": ("Activate LensFlow", "LensFlow", "activate"),
    "DEACTIVATE": ("Deactivate LensFlow", "LensFlow", "deactivate"),
}


def trigger_of(event):
    """
    Normalised trigger of an event:
        {"type": "gesture", "gesture": "<name>"}  or  {"type": "manual"}
    """

    if not isinstance(event, dict):
        return {"type": "manual"}

    trigger = event.get("trigger")

    if isinstance(trigger, dict) and trigger.get("type"):
        return trigger

    gesture = (event.get("gesture") or "").strip()

    if gesture:
        return {"type": "gesture", "gesture": gesture}

    return {"type": "manual"}


def gesture_of(event):
    """The gesture that triggers this event, or None."""

    trigger = trigger_of(event)

    if trigger["type"] == "gesture":
        return trigger.get("gesture")

    return None


def events_for_gesture(events, gesture):
    """All events triggered by `gesture`, in order."""

    return [
        event
        for event in events or []
        if gesture and gesture_of(event) == gesture
    ]


def profile_events(profile):
    """Convert a built-in profile's {gesture: action_name} map to events."""

    events = []

    for gesture, action_name in (profile or {}).get("gesture_map", {}).items():

        name, action, value = PROFILE_ACTIONS.get(
            action_name,
            (action_name, "Run Flow", action_name),
        )

        events.append({
            "name": name,
            "gesture": gesture,
            "action": action,
            "value": value,
        })

    return events


def parse_hotkey(value):
    """"ctrl+shift+t" -> ["ctrl", "shift", "t"]"""

    keys = [
        key.strip().lower()
        for key in (value or "").replace(" ", "").split("+")
    ]

    keys = [key for key in keys if key]

    if not keys:
        raise ValueError("No keys given. Use something like ctrl+shift+t.")

    return keys


def powerpoint_command(value):

    command = POWERPOINT_COMMANDS.get((value or "").strip().lower())

    if command is None:
        raise ValueError(
            f'Unknown PowerPoint command "{value}". '
            "Use next, previous, start or end."
        )

    return command

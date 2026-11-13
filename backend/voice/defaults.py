"""
Give Presentation Studio the standard voice phrases the first time voice
is used, so "Hey Wield, next slide" works without setting anything up.

Done once per user (remembered in settings): if they later remove the
phrases in Gesture Studio, they are not added back.
"""

from backend.settings.settings_manager import SettingsManager
from backend.voice.commands import is_voice_trigger, voice_trigger

FLAG = "voice_defaults_added"

PRESENTATION_VOICE = {
    "next slide": "presentation_next",
    "previous slide": "presentation_previous",
    "start presentation": "presentation_start",
    "end presentation": "presentation_end",
}


def add_default_voice_phrases(profile_manager, settings=None):
    """
    Add the standard phrases to the loaded presentation profile if it has
    no voice triggers and this hasn't been done before. Returns the list of
    phrases added (empty if nothing changed).
    """
    settings = settings or SettingsManager()

    if settings.get_setting(FLAG):
        return []

    gesture_map = profile_manager.get_gesture_map()

    if any(is_voice_trigger(t) for t in gesture_map):
        settings.set_setting(FLAG, True)
        return []

    added = []
    for phrase, action in PRESENTATION_VOICE.items():
        trigger = voice_trigger(phrase)
        if trigger not in gesture_map:
            gesture_map[trigger] = action
            added.append(phrase)

    if added:
        profile_manager.save_profile()

    settings.set_setting(FLAG, True)
    return added

"""The user's name, for greetings. Set in Settings; defaults to the
computer's account name (never a hardcoded person)."""

import getpass

from backend.settings.settings_manager import SettingsManager


KEY = "display_name"


def default_name():
    try:
        name = getpass.getuser()
    except Exception:
        return ""
    # "praveena.kiran" / "praveena_k" -> "Praveena"
    first = name.replace(".", " ").replace("_", " ").split()
    return first[0].capitalize() if first else ""


def display_name():
    try:
        stored = SettingsManager().get_setting(KEY)
    except Exception:
        stored = None
    return (stored or "").strip() or default_name()


def set_display_name(name):
    SettingsManager().set_setting(KEY, (name or "").strip())


def initials(name=None):
    parts = (name if name is not None else display_name()).split()
    return "".join(p[0] for p in parts[:2]).upper() or "?"

"""
"Start Wield when I sign in to Windows".

Uses the per-user Run key in the registry (no admin rights needed):
    HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run
Wield starts with --background, i.e. straight into the system tray.
Other systems: not supported (the option is disabled in the UI).
"""

import os
import sys
from backend.app_info import APP_NAME, LEGACY_NAMES


RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = APP_NAME


def is_supported():
    return sys.platform == "win32"


def launch_command():
    """The command Windows should run at sign-in."""

    if getattr(sys, "frozen", False):
        # The packaged Wield.exe
        return f'"{sys.executable}" --background'

    # Running from source: pythonw avoids a console window.
    python = sys.executable
    pythonw = os.path.join(os.path.dirname(python), "pythonw.exe")
    if os.path.isfile(pythonw):
        python = pythonw

    main = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main.py"))
    return f'"{python}" "{main}" --background'


def _has_value(key, name):
    import winreg
    try:
        winreg.QueryValueEx(key, name)
        return True
    except OSError:
        return False


def is_enabled():

    if not is_supported():
        return False

    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            return any(_has_value(key, n) for n in [VALUE_NAME] + LEGACY_NAMES)
    except OSError:
        return False


def migrate_legacy():
    """
    If start-at-sign-in was turned on under the old app name, re-register it
    under the new name (pointing at this install) and remove the old entry.
    """

    if not is_supported():
        return

    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            had_legacy = any(_has_value(key, n) for n in LEGACY_NAMES)
    except OSError:
        return

    if had_legacy:
        set_enabled(True)


def set_enabled(enabled):

    if not is_supported():
        raise RuntimeError("Starting at sign-in is only available on Windows.")

    import winreg

    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
    ) as key:
        if enabled:
            winreg.SetValueEx(key, VALUE_NAME, 0, winreg.REG_SZ, launch_command())
        else:
            try:
                winreg.DeleteValue(key, VALUE_NAME)
            except FileNotFoundError:
                pass

        # Old entries from before the rename are always removed.
        for name in LEGACY_NAMES:
            try:
                winreg.DeleteValue(key, name)
            except FileNotFoundError:
                pass

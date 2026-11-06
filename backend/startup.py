"""
"Start LensFlow when I sign in to Windows".

Uses the per-user Run key in the registry (no admin rights needed):
    HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run
LensFlow starts with --background, i.e. straight into the system tray.
Other systems: not supported (the option is disabled in the UI).
"""

import os
import sys


RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "LensFlow"


def is_supported():
    return sys.platform == "win32"


def launch_command():
    """The command Windows should run at sign-in."""

    if getattr(sys, "frozen", False):
        # The packaged LensFlow.exe
        return f'"{sys.executable}" --background'

    # Running from source: pythonw avoids a console window.
    python = sys.executable
    pythonw = os.path.join(os.path.dirname(python), "pythonw.exe")
    if os.path.isfile(pythonw):
        python = pythonw

    main = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main.py"))
    return f'"{python}" "{main}" --background'


def is_enabled():

    if not is_supported():
        return False

    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            winreg.QueryValueEx(key, VALUE_NAME)
            return True
    except OSError:
        return False


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

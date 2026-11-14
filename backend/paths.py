"""
Where Wield keeps its files.

Two locations matter:

* APP_DIR — where the app itself lives (the repo when running from source,
  or PyInstaller's unpack folder when running the packaged .exe). Anything
  here should be treated as read-only: in an installed app it often is.

* USER_DATA_DIR — a per-user, always-writable folder for everything the user
  changes: studios, settings, gesture profiles and custom gestures.
    Windows: %APPDATA%\\Wield
    macOS:   ~/Library/Application Support/Wield
    Linux:   ~/.config/wield
  Set the WIELD_DATA_DIR environment variable to override it (used by tests;
  the old LENSFLOW_DATA_DIR still works).

The JSON files in backend/config are the *defaults*. The first time a file
is needed it is copied into USER_DATA_DIR, and from then on the user's copy
is the one that is read and written.
"""

import os
import shutil
import sys

from backend.app_info import DATA_FOLDER, LEGACY_NAMES


APP_DIR = getattr(sys, "_MEIPASS", None) or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DEFAULT_CONFIG_DIR = os.path.join(APP_DIR, "backend", "config")

MODELS_DIR = os.path.join(APP_DIR, "backend", "models")


def _default_user_data_dir():

    override = os.environ.get("WIELD_DATA_DIR") or os.environ.get("LENSFLOW_DATA_DIR")

    if override:
        return override

    return _data_dir_for(DATA_FOLDER)


def _data_dir_for(folder):

    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base, folder)

    if sys.platform == "darwin":
        return os.path.expanduser(f"~/Library/Application Support/{folder}")

    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, folder.lower())


def _migrate_legacy_data(path):
    """
    The app used to be called LensFlow. If this user still has data under
    the old folder name and none under the new one, move it across once so
    their studios, gestures and notes come with them.
    """

    if os.path.exists(path):
        return

    for name in LEGACY_NAMES:
        old = _data_dir_for(name)
        if os.path.isdir(old) and os.path.abspath(old) != os.path.abspath(path):
            try:
                shutil.move(old, path)
                print(f"📦 Moved your data from {old} to {path}")
            except OSError as e:
                print(f"⚠ Could not move old data from {old}: {e}")
            return


def user_data_dir():
    """Return the per-user data folder, creating it if needed."""

    path = _default_user_data_dir()

    if not (os.environ.get("WIELD_DATA_DIR") or os.environ.get("LENSFLOW_DATA_DIR")):
        _migrate_legacy_data(path)

    os.makedirs(path, exist_ok=True)
    return path


def user_config_path(*parts):
    """
    Path to a writable config file, e.g. user_config_path("studios.json")
    or user_config_path("profiles", "coding.json").

    If the user does not have this file yet, the bundled default (if one
    exists) is copied in first. The returned path may not exist when there
    is no default — callers that create new files rely on that.
    """

    path = os.path.join(user_data_dir(), *parts)

    if not os.path.exists(path):

        default = os.path.join(DEFAULT_CONFIG_DIR, *parts)

        os.makedirs(os.path.dirname(path), exist_ok=True)

        if os.path.isfile(default):
            shutil.copyfile(default, path)

    return path


def user_config_dir(*parts):
    """
    Path to a writable config folder (e.g. "profiles"). Any bundled default
    files missing from the user's copy are copied in; existing user files
    are never overwritten.
    """

    path = os.path.join(user_data_dir(), *parts)
    os.makedirs(path, exist_ok=True)

    default_dir = os.path.join(DEFAULT_CONFIG_DIR, *parts)

    if os.path.isdir(default_dir):

        for name in os.listdir(default_dir):

            src = os.path.join(default_dir, name)
            dst = os.path.join(path, name)

            if os.path.isfile(src) and not os.path.exists(dst):
                shutil.copyfile(src, dst)

    return path


def model_path(filename):
    """Path to a bundled, read-only model file."""

    return os.path.join(MODELS_DIR, filename)

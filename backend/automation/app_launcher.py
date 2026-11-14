"""
Launch an application from what a user typed in an event, e.g. "chrome",
"Google Chrome", "chrome.exe" or a full path to an .exe.

On Windows, running "chrome" through the shell usually fails silently:
Chrome isn't on PATH. So we resolve the name first:

    1. an existing file path, used as-is
    2. an alias from apps.json ("chrome" -> path), if that file exists
    3. the usual install locations of common apps
    4. otherwise hand the name to Windows (ShellExecute), which also checks
       the "App Paths" registry that many installers fill in

If nothing works, AppLaunchError explains what to do instead of pretending
the launch succeeded.
"""

import os
import platform
import shutil
import subprocess


class AppLaunchError(Exception):
    pass


# Common apps and where Windows installers put them.
KNOWN_WINDOWS_APPS = {
    "chrome": [
        r"%ProgramFiles%\Google\Chrome\Application\chrome.exe",
        r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe",
        r"%LocalAppData%\Google\Chrome\Application\chrome.exe",
    ],
    "msedge": [
        r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe",
        r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe",
    ],
    "firefox": [
        r"%ProgramFiles%\Mozilla Firefox\firefox.exe",
        r"%ProgramFiles(x86)%\Mozilla Firefox\firefox.exe",
    ],
    "code": [
        r"%LocalAppData%\Programs\Microsoft VS Code\Code.exe",
        r"%ProgramFiles%\Microsoft VS Code\Code.exe",
    ],
    "spotify": [
        r"%AppData%\Spotify\Spotify.exe",
    ],
    "discord": [
        r"%LocalAppData%\Discord\Update.exe",
    ],
}

# Other names people type for the same apps.
ALIASES = {
    "google chrome": "chrome",
    "edge": "msedge",
    "microsoft edge": "msedge",
    "mozilla firefox": "firefox",
    "vscode": "code",
    "vs code": "code",
    "visual studio code": "code",
    "terminal": "wt",
    "windows terminal": "wt",
}

# Tried in order if an app can't be opened (Windows Terminal isn't on
# every PC; Command Prompt is).
FALLBACKS = {
    "wt": ["cmd"],
}


def _normalise(name):

    name = name.strip().strip('"').strip().lower()

    if name.endswith(".exe"):
        name = name[:-4]

    return ALIASES.get(name, name)


def resolve_windows_app(value, app_aliases=None, exists=os.path.isfile):
    """
    Return the best thing to hand to os.startfile() for `value`.
    `exists` is injectable for tests.
    """

    raw = value.strip().strip('"').strip()

    if exists(raw):
        return raw

    key = _normalise(raw)

    for alias, path in (app_aliases or {}).items():
        if _normalise(alias) == key:
            expanded = os.path.expandvars(path)
            if exists(expanded):
                return expanded

    for candidate in KNOWN_WINDOWS_APPS.get(key, []):
        expanded = os.path.expandvars(candidate)
        if exists(expanded):
            return expanded

    # Let Windows try (App Paths registry, PATH) with the real program name:
    # "chrome" -> "chrome.exe", "Terminal" (an alias) -> "wt.exe".
    if " " not in key and not os.path.splitext(key)[1]:
        return key + ".exe"

    return raw


def launch_app(value, app_aliases=None):
    """Launch an app or raise AppLaunchError with a user-friendly message."""

    if not value or not value.strip():
        raise AppLaunchError("No application specified.")

    system = platform.system()

    if system == "Windows":

        candidates = [value] + FALLBACKS.get(_normalise(value), [])
        last_error = None

        for candidate in candidates:
            target = resolve_windows_app(candidate, app_aliases)
            try:
                os.startfile(target)
                return target
            except OSError as e:
                last_error = e

        raise AppLaunchError(
            f'Couldn\'t find "{value}". Edit the event and use Browse '
            "to pick the app's .exe file."
        ) from last_error

    if system == "Darwin":

        result = subprocess.run(
            ["open", "-a", value],
            capture_output=True,
        )

        if result.returncode != 0:
            raise AppLaunchError(f'Couldn\'t find the app "{value}".')

        return value

    command = shutil.which(value) or (value if os.path.isfile(value) else None)

    if command is None:
        raise AppLaunchError(f'Couldn\'t find the app "{value}".')

    subprocess.Popen([command])
    return command

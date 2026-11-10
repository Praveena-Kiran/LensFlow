"""
The app's name and version, in one place.

To rename the app, change APP_NAME (every visible string, the window
title, tray, start-at-sign-in entry and log use it) and the .spec/workflow
file names. The app was called LensFlow before; LEGACY_* names let existing
installs move their data and settings across (see backend/paths.py and
backend/startup.py).
"""

APP_NAME = "Wield"
VERSION = "1.0.0"

DATA_FOLDER = "Wield"

# Earlier name(s): data folders / sign-in entries migrated on first run.
LEGACY_NAMES = ["LensFlow"]

# The repository (renamed from LensFlow; GitHub redirects the old address).
REPO_URL = "https://github.com/Praveena-Kiran/Wield"
ISSUES_URL = REPO_URL + "/issues/new"

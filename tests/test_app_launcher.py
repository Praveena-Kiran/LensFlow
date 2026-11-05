import os
import unittest
from unittest import mock

from backend.automation import app_launcher
from backend.automation.app_launcher import (
    AppLaunchError,
    launch_app,
    resolve_windows_app,
)

CHROME_X86 = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
CHROME_64 = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

WINDOWS_ENV = {
    "ProgramFiles": r"C:\Program Files",
    "ProgramFiles(x86)": r"C:\Program Files (x86)",
    "LocalAppData": r"C:\Users\me\AppData\Local",
    "AppData": r"C:\Users\me\AppData\Roaming",
}


def fake_expandvars(path):
    for key, value in WINDOWS_ENV.items():
        path = path.replace(f"%{key}%", value)
    return path


class ResolveTests(unittest.TestCase):

    def setUp(self):
        patcher = mock.patch.object(app_launcher.os.path, "expandvars", fake_expandvars)
        patcher.start()
        self.addCleanup(patcher.stop)

    def resolve(self, value, existing, aliases=None):
        return resolve_windows_app(value, aliases, exists=lambda p: p in existing)

    def test_finds_64_bit_chrome_when_alias_points_at_x86(self):
        aliases = {"chrome": CHROME_X86}
        for typed in ("chrome", "Chrome", "chrome.exe", "Google Chrome", ' "chrome" '):
            self.assertEqual(self.resolve(typed, {CHROME_64}, aliases), CHROME_64, typed)

    def test_alias_used_when_it_exists(self):
        self.assertEqual(self.resolve("chrome", {CHROME_X86}, {"chrome": CHROME_X86}), CHROME_X86)

    def test_full_path_used_as_is(self):
        path = r"D:\Tools\thing.exe"
        self.assertEqual(self.resolve(path, {path}), path)

    def test_vscode_names(self):
        code = r"C:\Users\me\AppData\Local\Programs\Microsoft VS Code\Code.exe"
        for typed in ("code", "VS Code", "vscode", "Visual Studio Code"):
            self.assertEqual(self.resolve(typed, {code}), code, typed)

    def test_unknown_name_falls_back_to_windows_lookup(self):
        self.assertEqual(self.resolve("notepad", set()), "notepad.exe")
        self.assertEqual(self.resolve("notepad.exe", set()), "notepad.exe")


class LaunchTests(unittest.TestCase):

    def test_empty_value(self):
        with self.assertRaises(AppLaunchError):
            launch_app("  ")

    @mock.patch.object(app_launcher.platform, "system", return_value="Windows")
    def test_windows_failure_is_reported(self, _system):
        with mock.patch.object(app_launcher.os, "startfile", create=True,
                               side_effect=FileNotFoundError("nope")):
            with self.assertRaises(AppLaunchError) as ctx:
                launch_app("definitely-not-an-app")
        self.assertIn("Browse", str(ctx.exception))

    @mock.patch.object(app_launcher.platform, "system", return_value="Windows")
    def test_windows_success_returns_target(self, _system):
        with mock.patch.object(app_launcher.os, "startfile", create=True) as startfile:
            self.assertEqual(launch_app("notepad"), "notepad.exe")
        startfile.assert_called_once_with("notepad.exe")

    @mock.patch.object(app_launcher.platform, "system", return_value="Linux")
    def test_linux_missing_app(self, _system):
        with mock.patch.object(app_launcher.shutil, "which", return_value=None):
            with self.assertRaises(AppLaunchError):
                launch_app("definitely-not-an-app")


if __name__ == "__main__":
    unittest.main()

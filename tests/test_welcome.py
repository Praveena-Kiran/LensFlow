import os
import tempfile
import unittest
from unittest import mock


class WelcomeTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        env = mock.patch.dict(os.environ, {"WIELD_DATA_DIR": self.tmp.name})
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("WIELD_NO_WELCOME", None)

    def test_shown_once(self):
        try:
            from frontend.components import welcome_dialog as wd
        except ImportError:
            self.skipTest("PySide6 not installed")
        self.assertTrue(wd.needs_welcome())
        wd.mark_welcomed()
        self.assertFalse(wd.needs_welcome())

    def test_can_be_disabled_for_automated_runs(self):
        try:
            from frontend.components import welcome_dialog as wd
        except ImportError:
            self.skipTest("PySide6 not installed")
        with mock.patch.dict(os.environ, {"WIELD_NO_WELCOME": "1"}):
            self.assertFalse(wd.needs_welcome())


if __name__ == "__main__":
    unittest.main()

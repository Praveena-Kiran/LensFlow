import os
import tempfile
import unittest
from unittest import mock

from backend.gestures import custom_gestures, motions


class GestureSettingsTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        patcher = mock.patch.dict(os.environ, {"LENSFLOW_DATA_DIR": self.tmp.name})
        patcher.start()
        self.addCleanup(patcher.stop)
        from backend.settings import gesture_settings
        self.gs = gesture_settings

    def test_defaults(self):
        values = self.gs.load()
        self.assertEqual(values["sensitivity"], 50)
        self.assertFalse(values["require_arm"])

    def test_middle_sensitivity_matches_calibrated_values(self):
        t = self.gs.thresholds({"sensitivity": 50, "hold_time": 0.0})
        self.assertAlmostEqual(t["pose_max_distance"], custom_gestures.DEFAULT_MAX_DISTANCE)
        self.assertAlmostEqual(t["motion_max_distance"], motions.DEFAULT_MAX_DISTANCE)
        self.assertAlmostEqual(t["swipe_min_straightness"], motions.SWIPE_MIN_STRAIGHTNESS)
        self.assertAlmostEqual(t["swipe_max_angle"], motions.SWIPE_MAX_ANGLE)
        self.assertAlmostEqual(t["min_confidence"], 0.60)

    def test_more_forgiving_loosens_everything(self):
        strict = self.gs.thresholds({"sensitivity": 0, "hold_time": 0.0})
        loose = self.gs.thresholds({"sensitivity": 100, "hold_time": 0.0})
        self.assertGreater(loose["pose_max_distance"], strict["pose_max_distance"])
        self.assertGreater(loose["motion_max_distance"], strict["motion_max_distance"])
        self.assertLess(loose["swipe_min_straightness"], strict["swipe_min_straightness"])
        self.assertLess(loose["min_confidence"], strict["min_confidence"])

    def test_save_and_reload(self):
        self.gs.save("require_arm", True)
        self.gs.save("sensitivity", 80)
        values = self.gs.load()
        self.assertTrue(values["require_arm"])
        self.assertEqual(values["sensitivity"], 80)
        with self.assertRaises(KeyError):
            self.gs.save("not_a_setting", 1)

    def test_bad_values_are_clamped(self):
        self.gs.save("sensitivity", 500)
        self.assertEqual(self.gs.load()["sensitivity"], 100)


if __name__ == "__main__":
    unittest.main()

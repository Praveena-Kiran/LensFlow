import unittest

from backend.automation.presentation_bindings import (
    binding,
    check_voice,
    set_gesture,
    set_voice,
)

THUMBS_UP = "👍 Thumbs Up"
THUMBS_DOWN = "👎 Thumbs Down"
PEACE = "✌️ Peace"


def sample_map():
    return {
        PEACE: "presentation_start",
        THUMBS_UP: "presentation_next",
        "Swipe right": "presentation_next",
        THUMBS_DOWN: "presentation_previous",
        "🎤 next slide": "presentation_next",
        "🎤 previous slide": "presentation_previous",
    }


class BindingTests(unittest.TestCase):

    def test_main_gesture_and_extras(self):
        b = binding(sample_map(), "presentation_next")
        self.assertEqual(b["gesture"], THUMBS_UP)
        self.assertEqual(b["more_gestures"], 1)
        self.assertEqual(b["phrase"], "next slide")
        self.assertEqual(b["more_phrases"], 0)

    def test_empty_action(self):
        b = binding(sample_map(), "presentation_end")
        self.assertEqual(b, {"gesture": None, "more_gestures": 0, "phrase": "", "more_phrases": 0})


class SetGestureTests(unittest.TestCase):

    def test_replaces_main_gesture_and_keeps_extras(self):
        m = sample_map()
        self.assertEqual(set_gesture(m, "presentation_next", "forward"), "")
        self.assertNotIn(THUMBS_UP, m)
        self.assertEqual(m["forward"], "presentation_next")
        self.assertEqual(m["Swipe right"], "presentation_next")   # extra kept
        self.assertEqual(m["🎤 next slide"], "presentation_next")  # voice kept

    def test_taking_a_gesture_from_another_action(self):
        m = sample_map()
        note = set_gesture(m, "presentation_end", THUMBS_DOWN)
        self.assertEqual(m[THUMBS_DOWN], "presentation_end")
        self.assertIn("Previous slide", note)
        self.assertIsNone(binding(m, "presentation_previous")["gesture"])

    def test_clearing(self):
        m = sample_map()
        set_gesture(m, "presentation_start", None)
        self.assertNotIn(PEACE, m)

    def test_same_gesture_is_a_no_op(self):
        m = sample_map()
        self.assertEqual(set_gesture(m, "presentation_next", THUMBS_UP), "")
        self.assertEqual(m, sample_map())


class SetVoiceTests(unittest.TestCase):

    def test_replace_phrase(self):
        m = sample_map()
        ok, _ = set_voice(m, "presentation_next", "  Onwards, Please! ")
        self.assertTrue(ok)
        self.assertNotIn("🎤 next slide", m)
        self.assertEqual(m["🎤 onwards please"], "presentation_next")

    def test_add_phrase_to_action_without_one(self):
        m = sample_map()
        self.assertTrue(set_voice(m, "presentation_end", "finish up")[0])
        self.assertEqual(m["🎤 finish up"], "presentation_end")

    def test_clear_phrase(self):
        m = sample_map()
        self.assertTrue(set_voice(m, "presentation_next", "")[0])
        self.assertNotIn("🎤 next slide", m)

    def test_duplicate_phrase_is_refused(self):
        m = sample_map()
        ok, message = set_voice(m, "presentation_end", "previous slide")
        self.assertFalse(ok)
        self.assertIn("Previous slide", message)
        self.assertEqual(m, sample_map())

    def test_bad_phrases(self):
        m = sample_map()
        for phrase in ("go", "hey wield", "one two three four five six"):
            self.assertFalse(check_voice(m, "presentation_end", phrase)[0], phrase)

    def test_keeping_own_phrase_is_fine(self):
        m = sample_map()
        self.assertEqual(check_voice(m, "presentation_next", "Next slide"), (True, ""))


if __name__ == "__main__":
    unittest.main()

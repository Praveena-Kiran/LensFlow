"""Every theme has every token, and its text is readable (WCAG AA contrast)."""

import unittest

from frontend.styles.theme import THEMES


def luminance(hex_colour):
    h = hex_colour.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    lin = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


class ThemeTests(unittest.TestCase):

    def test_all_themes_define_the_same_tokens(self):
        keys = set(THEMES["dark"])
        for name, palette in THEMES.items():
            self.assertEqual(set(palette), keys, name)

    def test_text_is_readable(self):
        for name, t in THEMES.items():
            for bg in ("BG_DARK", "SURFACE", "SURFACE_HOVER"):
                for fg in ("PRIMARY_TEXT", "SECONDARY_TEXT", "TEXT_MUTED"):
                    with self.subTest(theme=name, fg=fg, bg=bg):
                        self.assertGreaterEqual(contrast(t[fg], t[bg]), 4.5)

    def test_button_text_is_readable(self):
        for name, t in THEMES.items():
            with self.subTest(theme=name):
                self.assertGreaterEqual(contrast(t["ON_PRIMARY"], t["PRIMARY"]), 4.5)

    def test_accent_is_visible_against_the_background(self):
        # Non-text UI (focus rings, sliders) needs 3:1.
        for name, t in THEMES.items():
            with self.subTest(theme=name):
                self.assertGreaterEqual(contrast(t["PRIMARY"], t["BG_DARK"]), 3.0)


if __name__ == "__main__":
    unittest.main()

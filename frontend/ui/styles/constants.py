"""LensFlow Design System - System Constants

Defines animation timings, component sizing standards, and layout constraints.
"""

from PySide6.QtCore import QEasingCurve

# Animation Durations (ms)
ANIM_FAST = 150
ANIM_NORMAL = 250
ANIM_SLOW = 400

# Easing Curves
EASING_DEFAULT = QEasingCurve.Type.OutCubic
EASING_SPRING = QEasingCurve.Type.OutBack
EASING_SMOOTH = QEasingCurve.Type.InOutQuad

# Component Dimensions
SIDEBAR_COLLAPSED_WIDTH = 64
SIDEBAR_EXPANDED_WIDTH = 240
BUTTON_HEIGHT_SM = 32
BUTTON_HEIGHT_MD = 40
BUTTON_HEIGHT_LG = 48
CARD_MIN_WIDTH = 280
CARD_MIN_HEIGHT = 160
SEARCH_BAR_HEIGHT = 42
TOGGLE_WIDTH = 48
TOGGLE_HEIGHT = 26

# Drop Shadow Presets
SHADOW_SOFT_BLUR = 20
SHADOW_SOFT_OFFSET_Y = 6
SHADOW_HOVER_BLUR = 30
SHADOW_HOVER_OFFSET_Y = 10

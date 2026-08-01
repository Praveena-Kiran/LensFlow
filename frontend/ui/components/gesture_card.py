"""LensFlow Design System - GestureCard Component

Reusable card featuring a large gesture outline icon, gesture name, and sleek minimal styling.
"""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from frontend.ui.components.glass_card import GlassCard
from frontend.ui.components.icons import VectorIcon
from frontend.ui.styles.colors import TEXT_PRIMARY, TEXT_SECONDARY, ACCENT
from frontend.ui.styles.spacing import SPACE_16, RADIUS_LG
from frontend.ui.animations.animation_utils import HoverEffectFilter


class GestureCard(GlassCard):
    """Reusable minimal Gesture Card widget."""

    def __init__(
        self,
        gesture_name: str = "Swipe Left",
        icon_type: str = VectorIcon.GESTURE,
        parent: Optional[QWidget] = None
    ):
        super().__init__(border_radius=RADIUS_LG, padding=SPACE_16, parent=parent)
        self.setFixedSize(140, 140)

        # Center Layout
        layout = self.get_layout()
        layout.setContentsMargins(SPACE_16, SPACE_16, SPACE_16, SPACE_16)
        layout.setSpacing(SPACE_16)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Large Gesture Icon
        self.gesture_icon = VectorIcon(icon_type=icon_type, color=ACCENT, size=40)
        layout.addWidget(self.gesture_icon, 0, Qt.AlignmentFlag.AlignCenter)

        # Gesture Name
        self.name_label = QLabel(gesture_name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-weight: 600; font-size: 13px;")
        layout.addWidget(self.name_label, 0, Qt.AlignmentFlag.AlignCenter)

        # Hover filter
        self._hover_filter = HoverEffectFilter(
            self,
            on_enter=lambda: self.setStyleSheet(f"QFrame#GlassCard {{ background-color: rgba(30, 30, 40, 0.90); border: 1px solid {ACCENT}; border-radius: {self.border_radius}px; }}"),
            on_leave=self._apply_style
        )

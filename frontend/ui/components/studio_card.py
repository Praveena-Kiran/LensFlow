"""LensFlow Design System - StudioCard Component

Reusable Studio card displaying icon, title, subtitle, hover lift animation,
and a primary action button.
"""

from typing import Optional, Callable
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtWidgets import QLabel, QHBoxLayout, QVBoxLayout, QWidget
from frontend.ui.components.glass_card import GlassCard
from frontend.ui.components.buttons import PrimaryButton
from frontend.ui.components.icons import VectorIcon
from frontend.ui.styles.colors import TEXT_PRIMARY, TEXT_SECONDARY
from frontend.ui.styles.spacing import SPACE_8, SPACE_16, RADIUS_LG
from frontend.ui.animations.animation_utils import HoverEffectFilter


class StudioCard(GlassCard):
    """Reusable Studio Card with icon, title, subtitle, hover elevation, and action button."""

    action_clicked = Signal()

    def __init__(
        self,
        title: str = "Studio Workflow",
        subtitle: str = "Create automated workspace routines and triggers.",
        icon_type: str = VectorIcon.STUDIO,
        button_text: str = "Launch Studio",
        on_action: Optional[Callable[[], None]] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(border_radius=RADIUS_LG, padding=SPACE_16, parent=parent)
        self.setMinimumWidth(280)
        self.setMinimumHeight(180)

        # Header Layout (Icon + Title)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(SPACE_12 := 12)

        self.icon_widget = VectorIcon(icon_type=icon_type, color="#3B82F6", size=28)
        header_layout.addWidget(self.icon_widget, 0, Qt.AlignmentFlag.AlignTop)

        title_box = QVBoxLayout()
        title_box.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 16px; font-weight: 600;")
        title_box.addWidget(self.title_label)

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; line-height: 1.4;")
        title_box.addWidget(self.subtitle_label)

        header_layout.addLayout(title_box, 1)
        self.get_layout().addLayout(header_layout)

        self.get_layout().addStretch(1)

        # Bottom Action Layout
        action_layout = QHBoxLayout()
        action_layout.addStretch()

        self.action_button = PrimaryButton(button_text)
        if on_action:
            self.action_button.clicked.connect(on_action)
        self.action_button.clicked.connect(self.action_clicked.emit)

        action_layout.addWidget(self.action_button)
        self.get_layout().addLayout(action_layout)

        # Smooth hover effect setup
        self._hover_filter = HoverEffectFilter(
            self,
            on_enter=self._on_hover_enter,
            on_leave=self._on_hover_leave
        )

    def _on_hover_enter(self):
        """Card hover lift feedback."""
        self.setStyleSheet(f"""
            QFrame#GlassCard {{
                background-color: rgba(28, 28, 36, 0.85);
                border: 1px solid rgba(59, 130, 246, 0.4);
                border-radius: {self.border_radius}px;
            }}
        """)

    def _on_hover_leave(self):
        """Restores normal card background."""
        self._apply_style()

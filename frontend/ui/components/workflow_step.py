"""LensFlow Design System - WorkflowStep Component

Reusable Workflow Step card featuring rounded glass corners, step icon, step title,
and drag handle placeholder.
"""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from frontend.ui.components.glass_card import GlassCard
from frontend.ui.components.icons import VectorIcon
from frontend.ui.styles.colors import TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, ACCENT
from frontend.ui.styles.spacing import SPACE_16, RADIUS_MD
from frontend.ui.animations.animation_utils import HoverEffectFilter


class WorkflowStep(GlassCard):
    """Reusable Workflow Step Card component."""

    def __init__(
        self,
        step_number: int = 1,
        title: str = "Trigger Camera Feed",
        description: str = "Captures current screen state upon gesture signal",
        icon_type: str = VectorIcon.WORKFLOW,
        parent: Optional[QWidget] = None
    ):
        super().__init__(border_radius=RADIUS_MD, padding=SPACE_16, parent=parent)
        self.setFixedHeight(80)
        self.setMinimumWidth(300)

        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(SPACE_16)

        # Drag Handle Placeholder
        self.drag_handle = VectorIcon(icon_type=VectorIcon.DRAG_HANDLE, color=TEXT_MUTED, size=16)
        self.drag_handle.setCursor(Qt.CursorShape.SizeAllCursor)
        row_layout.addWidget(self.drag_handle, 0, Qt.AlignmentFlag.AlignCenter)

        # Step Number Badge / Icon
        self.icon_widget = VectorIcon(icon_type=icon_type, color=ACCENT, size=24)
        row_layout.addWidget(self.icon_widget, 0, Qt.AlignmentFlag.AlignCenter)

        # Title & Description Box
        text_box = QVBoxLayout()
        text_box.setSpacing(2)

        self.title_label = QLabel(f"{step_number}. {title}")
        self.title_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-weight: 600; font-size: 13px;")
        text_box.addWidget(self.title_label)

        self.desc_label = QLabel(description)
        self.desc_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        text_box.addWidget(self.desc_label)

        row_layout.addLayout(text_box, 1)

        self.get_layout().addLayout(row_layout)

        # Hover Effect
        self._hover_filter = HoverEffectFilter(
            self,
            on_enter=lambda: self.setStyleSheet(f"QFrame#GlassCard {{ background-color: rgba(28, 28, 38, 0.85); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: {self.border_radius}px; }}"),
            on_leave=self._apply_style
        )

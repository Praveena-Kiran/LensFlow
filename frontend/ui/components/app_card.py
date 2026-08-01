"""LensFlow Design System - ApplicationCard Component

Reusable Application card featuring app icon, app name, status indicator badge,
and a drag handle placeholder.
"""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from frontend.ui.components.glass_card import GlassCard
from frontend.ui.components.icons import VectorIcon
from frontend.ui.styles.colors import TEXT_PRIMARY, TEXT_SECONDARY, SUCCESS, WARNING, TEXT_MUTED
from frontend.ui.styles.spacing import SPACE_8, SPACE_16, RADIUS_MD
from frontend.ui.animations.animation_utils import HoverEffectFilter


class ApplicationCard(GlassCard):
    """Reusable Application Card component."""

    STATUS_ACTIVE = "active"
    STATUS_IDLE = "idle"
    STATUS_OFFLINE = "offline"

    def __init__(
        self,
        app_name: str = "VS Code",
        status: str = STATUS_ACTIVE,
        icon_type: str = VectorIcon.APP,
        parent: Optional[QWidget] = None
    ):
        super().__init__(border_radius=RADIUS_MD, padding=SPACE_16, parent=parent)
        self.setFixedHeight(72)
        self.setMinimumWidth(260)

        # Card Content Row Layout
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(SPACE_16)

        # Drag Handle Placeholder
        self.drag_handle = VectorIcon(icon_type=VectorIcon.DRAG_HANDLE, color=TEXT_MUTED, size=16)
        self.drag_handle.setCursor(Qt.CursorShape.SizeAllCursor)
        row_layout.addWidget(self.drag_handle, 0, Qt.AlignmentFlag.AlignCenter)

        # App Icon Placeholder
        self.app_icon = VectorIcon(icon_type=icon_type, color="#3B82F6", size=24)
        row_layout.addWidget(self.app_icon, 0, Qt.AlignmentFlag.AlignCenter)

        # App Name Label
        self.name_label = QLabel(app_name)
        self.name_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-weight: 600; font-size: 14px;")
        row_layout.addWidget(self.name_label, 1, Qt.AlignmentFlag.AlignVCenter)

        # Status Badge Widget
        self.status_container = QWidget()
        status_layout = QHBoxLayout(self.status_container)
        status_layout.setContentsMargins(8, 4, 10, 4)
        status_layout.setSpacing(6)

        self.status_dot = QFrame()
        self.status_dot.setFixedSize(8, 8)
        self.status_dot.setObjectName("StatusDot")

        self.status_label = QLabel()
        self.status_label.setStyleSheet("font-size: 11px; font-weight: 500;")

        status_layout.addWidget(self.status_dot)
        status_layout.addWidget(self.status_label)

        row_layout.addWidget(self.status_container, 0, Qt.AlignmentFlag.AlignVCenter)

        self.get_layout().addLayout(row_layout)
        self.set_status(status)

        # Hover filter
        self._hover_filter = HoverEffectFilter(
            self,
            on_enter=lambda: self.setStyleSheet(f"QFrame#GlassCard {{ background-color: rgba(28, 28, 36, 0.85); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: {self.border_radius}px; }}"),
            on_leave=self._apply_style
        )

    def set_status(self, status: str):
        """Updates the visual status badge (Active, Idle, Offline)."""
        self.status = status.lower()
        if self.status == self.STATUS_ACTIVE:
            color = SUCCESS
            text = "Active"
        elif self.status == self.STATUS_IDLE:
            color = WARNING
            text = "Idle"
        else:
            color = TEXT_MUTED
            text = "Offline"

        self.status_dot.setStyleSheet(f"background-color: {color}; border-radius: 4px;")
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: 500;")
        self.status_container.setStyleSheet(f"background-color: rgba(255, 255, 255, 0.04); border-radius: 10px;")

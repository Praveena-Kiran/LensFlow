"""LensFlow Design System - GlassCard Component

Reusable glassmorphism container featuring rounded corners, subtle translucent background,
soft border, and drop shadow effect.
"""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QVBoxLayout, QWidget
from PySide6.QtGui import QColor
from frontend.ui.styles.colors import GLASS_BG, GLASS_BORDER, GLASS_SHADOW, get_qcolor
from frontend.ui.styles.spacing import RADIUS_LG, SPACE_16


class GlassCard(QFrame):
    """Premium glassmorphism card container widget."""

    def __init__(
        self,
        border_radius: int = RADIUS_LG,
        padding: int = SPACE_16,
        enable_shadow: bool = True,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.border_radius = border_radius
        self.padding = padding
        self.enable_shadow = enable_shadow

        self.setObjectName("GlassCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # Internal Layout
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(padding, padding, padding, padding)
        self._layout.setSpacing(SPACE_16)

        # Apply Base Glassmorphism Styling
        self._apply_style()

        # Apply Soft Drop Shadow Effect
        if self.enable_shadow:
            self._shadow = QGraphicsDropShadowEffect(self)
            self._shadow.setBlurRadius(24)
            self._shadow.setOffset(0, 8)
            self._shadow.setColor(get_qcolor(GLASS_SHADOW))
            self.setGraphicsEffect(self._shadow)

    def _apply_style(self):
        """Applies stylesheet for glass background and subtle border."""
        self.setStyleSheet(f"""
            QFrame#GlassCard {{
                background-color: {GLASS_BG};
                border: 1px solid {GLASS_BORDER};
                border-radius: {self.border_radius}px;
            }}
            QFrame#GlassCard:hover {{
                border: 1px solid rgba(255, 255, 255, 0.20);
            }}
        """)

    def set_padding(self, padding: int):
        """Updates internal content layout margins."""
        self.padding = padding
        self._layout.setContentsMargins(padding, padding, padding, padding)

    def add_widget(self, widget: QWidget):
        """Helper to add child widget to card layout."""
        self._layout.addWidget(widget)

    def get_layout(self) -> QVBoxLayout:
        """Returns internal vertical layout."""
        return self._layout

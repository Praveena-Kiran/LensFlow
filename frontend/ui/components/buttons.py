"""LensFlow Design System - Button Components

Implements PrimaryButton, SecondaryButton, and GhostButton with electric blue accents,
glass aesthetics, smooth hover/pressed animations, and disabled state styling.
"""

from typing import Optional
from PySide6.QtCore import Qt, QPropertyAnimation, QRect, QEvent
from PySide6.QtWidgets import QPushButton, QWidget
from frontend.ui.styles.colors import (
    ACCENT, ACCENT_HOVER, ACCENT_PRESSED, ACCENT_GLOW,
    GLASS_BG, GLASS_BORDER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_DISABLED
)
from frontend.ui.styles.spacing import RADIUS_MD, SPACE_16, SPACE_8
from frontend.ui.styles.constants import BUTTON_HEIGHT_MD, ANIM_FAST, EASING_SPRING


class BaseButton(QPushButton):
    """Base button featuring press scale feedback and consistent cursor state."""

    def __init__(self, text: str = "", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(BUTTON_HEIGHT_MD)
        self.setMinimumWidth(100)

        # Scale press animation setup
        self._anim = QPropertyAnimation(self, b"geometry", self)
        self._anim.setDuration(ANIM_FAST)
        self._anim.setEasingCurve(EASING_SPRING)
        self._normal_rect: Optional[QRect] = None

    def mousePressEvent(self, event):
        if self.isEnabled():
            rect = self.geometry()
            self._normal_rect = rect
            scaled_rect = QRect(
                rect.x() + int(rect.width() * 0.02),
                rect.y() + int(rect.height() * 0.02),
                int(rect.width() * 0.96),
                int(rect.height() * 0.96)
            )
            self._anim.stop()
            self._anim.setStartValue(rect)
            self._anim.setEndValue(scaled_rect)
            self._anim.start()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.isEnabled() and self._normal_rect:
            self._anim.stop()
            self._anim.setStartValue(self.geometry())
            self._anim.setEndValue(self._normal_rect)
            self._anim.start()
        super().mouseReleaseEvent(event)


class PrimaryButton(BaseButton):
    """Filled electric blue primary call-to-action button."""

    def __init__(self, text: str = "", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.setObjectName("PrimaryButton")
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(f"""
            QPushButton#PrimaryButton {{
                background-color: {ACCENT};
                color: {TEXT_PRIMARY};
                border: none;
                border-radius: {RADIUS_MD}px;
                font-weight: 600;
                font-size: 13px;
                padding: 0px {SPACE_16}px;
            }}
            QPushButton#PrimaryButton:hover {{
                background-color: {ACCENT_HOVER};
            }}
            QPushButton#PrimaryButton:pressed {{
                background-color: {ACCENT_PRESSED};
            }}
            QPushButton#PrimaryButton:disabled {{
                background-color: #27272A;
                color: {TEXT_DISABLED};
            }}
        """)


class SecondaryButton(BaseButton):
    """Glass style button with subtle border and smooth hover transition."""

    def __init__(self, text: str = "", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.setObjectName("SecondaryButton")
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(f"""
            QPushButton#SecondaryButton {{
                background-color: {GLASS_BG};
                color: {TEXT_PRIMARY};
                border: 1px solid {GLASS_BORDER};
                border-radius: {RADIUS_MD}px;
                font-weight: 500;
                font-size: 13px;
                padding: 0px {SPACE_16}px;
            }}
            QPushButton#SecondaryButton:hover {{
                background-color: rgba(38, 38, 48, 0.85);
                border: 1px solid rgba(255, 255, 255, 0.25);
                color: {TEXT_PRIMARY};
            }}
            QPushButton#SecondaryButton:pressed {{
                background-color: rgba(20, 20, 26, 0.95);
            }}
            QPushButton#SecondaryButton:disabled {{
                background-color: transparent;
                border: 1px solid rgba(255, 255, 255, 0.05);
                color: {TEXT_DISABLED};
            }}
        """)


class GhostButton(BaseButton):
    """Transparent button with minimal hover highlight for subtle actions."""

    def __init__(self, text: str = "", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.setObjectName("GhostButton")
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(f"""
            QPushButton#GhostButton {{
                background-color: transparent;
                color: {TEXT_SECONDARY};
                border: none;
                border-radius: {RADIUS_MD}px;
                font-weight: 500;
                font-size: 13px;
                padding: 0px {SPACE_16}px;
            }}
            QPushButton#GhostButton:hover {{
                background-color: rgba(255, 255, 255, 0.08);
                color: {TEXT_PRIMARY};
            }}
            QPushButton#GhostButton:pressed {{
                background-color: rgba(255, 255, 255, 0.14);
            }}
            QPushButton#GhostButton:disabled {{
                background-color: transparent;
                color: {TEXT_DISABLED};
            }}
        """)

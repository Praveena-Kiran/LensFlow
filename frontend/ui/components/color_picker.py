"""LensFlow Design System - ColorPicker Component

Reusable Color Picker featuring circular color swatches, smooth selection ring animations,
and color selection signals.
"""

from typing import Optional, List
from PySide6.QtCore import Qt, Signal, Property, QPropertyAnimation, QRectF
from PySide6.QtGui import QPainter, QColor, QBrush, QPen
from PySide6.QtWidgets import QWidget, QHBoxLayout, QAbstractButton
from frontend.ui.styles.colors import get_qcolor, ACCENT
from frontend.ui.styles.constants import ANIM_FAST, EASING_SPRING


class ColorSwatch(QAbstractButton):
    """Individual circular color swatch widget with selection ring animation."""

    def __init__(self, color_hex: str, size: int = 28, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.color_hex = color_hex
        self.swatch_size = size
        self.setFixedSize(size + 8, size + 8)  # Space for ring
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Selection animation ring factor (0.0 to 1.0)
        self._ring_factor = 0.0

        self._anim = QPropertyAnimation(self, b"ring_factor", self)
        self._anim.setDuration(ANIM_FAST)
        self._anim.setEasingCurve(EASING_SPRING)

    def get_ring_factor(self) -> float:
        return self._ring_factor

    def set_ring_factor(self, val: float):
        self._ring_factor = val
        self.update()

    ring_factor = Property(float, get_ring_factor, set_ring_factor)

    def set_selected(self, selected: bool):
        self.setChecked(selected)
        self._anim.stop()
        self._anim.setStartValue(self._ring_factor)
        self._anim.setEndValue(1.0 if selected else 0.0)
        self._anim.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = float(self.width()), float(self.height())
        cx, cy = w / 2.0, h / 2.0
        swatch_color = get_qcolor(self.color_hex)

        # Outer Selection Ring
        if self._ring_factor > 0.001:
            ring_pen = QPen(swatch_color, 2.0 * self._ring_factor)
            painter.setPen(ring_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            ring_radius = (self.swatch_size + 4) / 2.0
            painter.drawEllipse(QRectF(cx - ring_radius, cy - ring_radius, ring_radius * 2, ring_radius * 2))

        # Inner Solid Swatch Circle
        swatch_radius = (self.swatch_size - 4 * (1.0 - self._ring_factor)) / 2.0
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(swatch_color))
        painter.drawEllipse(QRectF(cx - swatch_radius, cy - swatch_radius, swatch_radius * 2, swatch_radius * 2))


class ColorPicker(QWidget):
    """Reusable circular color picker component."""

    color_selected = Signal(str)

    DEFAULT_PALETTE = [
        "#3B82F6",  # Electric Blue
        "#10B981",  # Emerald
        "#8B5CF6",  # Purple
        "#EC4899",  # Pink
        "#F59E0B",  # Amber
        "#06B6D4",  # Cyan
        "#EF4444",  # Red
        "#64748B",  # Slate
    ]

    def __init__(
        self,
        colors: Optional[List[str]] = None,
        selected_color: Optional[str] = None,
        swatch_size: int = 24,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.swatch_size = swatch_size
        self.swatches: List[ColorSwatch] = []
        self.current_color: Optional[str] = None

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(8)

        palette = colors or self.DEFAULT_PALETTE
        for color_hex in palette:
            self.add_color(color_hex)

        initial = selected_color or palette[0]
        self.select_color(initial)

    def add_color(self, color_hex: str):
        """Adds a color swatch to the picker."""
        swatch = ColorSwatch(color_hex, size=self.swatch_size, parent=self)

        def _on_click():
            self.select_color(color_hex)

        swatch.clicked.connect(_on_click)
        self._layout.addWidget(swatch)
        self.swatches.append(swatch)

    def select_color(self, color_hex: str):
        """Sets selected color by hex string."""
        self.current_color = color_hex
        for swatch in self.swatches:
            is_match = (swatch.color_hex.lower() == color_hex.lower())
            swatch.set_selected(is_match)

        self.color_selected.emit(color_hex)

    def get_selected_color(self) -> Optional[str]:
        """Returns currently selected hex color string."""
        return self.current_color

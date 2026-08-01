"""LensFlow Design System - ToggleSwitch Component

Modern iOS/Linear style animated toggle switch with smooth knob translation,
glow track background, and custom checked state signals.
"""

from typing import Optional
from PySide6.QtCore import Qt, Property, QPropertyAnimation, Signal, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QBrush, QPen
from PySide6.QtWidgets import QAbstractButton, QWidget
from frontend.ui.styles.colors import ACCENT, ELEVATED, get_qcolor
from frontend.ui.styles.constants import TOGGLE_WIDTH, TOGGLE_HEIGHT, ANIM_FAST, EASING_DEFAULT


class ToggleSwitch(QAbstractButton):
    """Modern animated toggle switch widget."""

    toggled_state = Signal(bool)

    def __init__(self, checked: bool = False, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(TOGGLE_WIDTH, TOGGLE_HEIGHT)

        # Handle Knob Animation Position (0.0 to 1.0)
        self._knob_position = 1.0 if checked else 0.0

        self._anim = QPropertyAnimation(self, b"knob_position", self)
        self._anim.setDuration(ANIM_FAST)
        self._anim.setEasingCurve(EASING_DEFAULT)

        self.toggled.connect(self._on_toggled)

    def get_knob_position(self) -> float:
        return self._knob_position

    def set_knob_position(self, pos: float):
        self._knob_position = pos
        self.update()

    # Qt Property for animation driver
    knob_position = Property(float, get_knob_position, set_knob_position)

    def _on_toggled(self, checked: bool):
        self._anim.stop()
        self._anim.setStartValue(self._knob_position)
        self._anim.setEndValue(1.0 if checked else 0.0)
        self._anim.start()
        self.toggled_state.emit(checked)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = float(self.width()), float(self.height())
        radius = h / 2.0

        # Background track color interpolation between OFF (#1C1C22) and ON (#3B82F6)
        off_color = get_qcolor("#1C1C22")
        on_color = get_qcolor(ACCENT)

        r = off_color.red() + int((on_color.red() - off_color.red()) * self._knob_position)
        g = off_color.green() + int((on_color.green() - off_color.green()) * self._knob_position)
        b = off_color.blue() + int((on_color.blue() - off_color.blue()) * self._knob_position)
        bg_color = QColor(r, g, b)

        # Draw Background Track
        track_rect = QRectF(0, 0, w, h)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(track_rect, radius, radius)

        # Draw Track Border
        border_color = QColor(255, 255, 255, int(20 + 30 * self._knob_position))
        painter.setPen(QPen(border_color, 1.0))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(track_rect, radius, radius)

        # Draw Circular Knob
        knob_margin = 3.0
        knob_diameter = h - 2 * knob_margin
        min_x = knob_margin
        max_x = w - knob_margin - knob_diameter
        knob_x = min_x + (max_x - min_x) * self._knob_position
        knob_y = knob_margin

        knob_rect = QRectF(knob_x, knob_y, knob_diameter, knob_diameter)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawEllipse(knob_rect)

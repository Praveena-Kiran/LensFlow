"""LensFlow Design System - Helper Animation Utilities

Reusable PySide6 animation utilities for Fade, Hover, Scale, and Slide transitions.
"""

from typing import Optional, Callable
from PySide6.QtCore import (
    QObject, QPropertyAnimation, QParallelAnimationGroup,
    QEasingCurve, QPoint, QRect, QEvent, Qt, Signal
)
from PySide6.QtWidgets import QWidget, QGraphicsOpacityEffect
from frontend.ui.styles.constants import ANIM_FAST, ANIM_NORMAL, EASING_DEFAULT, EASING_SPRING


class FadeAnimation(QObject):
    """Reusable opacity fade in / fade out animation helper."""

    finished = Signal()

    def __init__(self, widget: QWidget, duration: int = ANIM_NORMAL, parent: Optional[QObject] = None):
        super().__init__(parent or widget)
        self.widget = widget
        self.duration = duration

        # Ensure graphic opacity effect is attached
        self.opacity_effect = widget.graphicsEffect()
        if not isinstance(self.opacity_effect, QGraphicsOpacityEffect):
            self.opacity_effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(self.opacity_effect)

        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity", self)
        self.anim.setDuration(self.duration)
        self.anim.setEasingCurve(EASING_DEFAULT)
        self.anim.finished.connect(self.finished.emit)

    def fade_in(self, start_val: float = 0.0, end_val: float = 1.0):
        """Triggers smooth fade-in transition."""
        self.anim.stop()
        self.widget.show()
        self.anim.setStartValue(start_val)
        self.anim.setEndValue(end_val)
        self.anim.start()

    def fade_out(self, hide_on_finish: bool = True):
        """Triggers smooth fade-out transition."""
        self.anim.stop()
        current_op = self.opacity_effect.opacity()
        self.anim.setStartValue(current_op)
        self.anim.setEndValue(0.0)

        if hide_on_finish:
            def _on_finish():
                self.widget.hide()
                try:
                    self.anim.finished.disconnect(_on_finish)
                except RuntimeError:
                    pass
            self.anim.finished.connect(_on_finish)

        self.anim.start()


class SlideAnimation(QObject):
    """Reusable translation slide animation helper for QWidgets."""

    finished = Signal()

    def __init__(self, widget: QWidget, duration: int = ANIM_NORMAL, parent: Optional[QObject] = None):
        super().__init__(parent or widget)
        self.widget = widget
        self.duration = duration
        self.anim = QPropertyAnimation(self.widget, b"pos", self)
        self.anim.setDuration(self.duration)
        self.anim.setEasingCurve(EASING_DEFAULT)
        self.anim.finished.connect(self.finished.emit)

    def slide_to(self, target_pos: QPoint, easing: QEasingCurve.Type = EASING_DEFAULT):
        """Slides widget from current position to target position."""
        self.anim.stop()
        self.anim.setEasingCurve(easing)
        self.anim.setStartValue(self.widget.pos())
        self.anim.setEndValue(target_pos)
        self.anim.start()

    def slide_by(self, dx: int, dy: int, easing: QEasingCurve.Type = EASING_DEFAULT):
        """Slides widget by horizontal and vertical delta offsets."""
        current_pos = self.widget.pos()
        target = QPoint(current_pos.x() + dx, current_pos.y() + dy)
        self.slide_to(target, easing=easing)


class HoverEffectFilter(QObject):
    """Event filter that triggers custom enter/leave callbacks for smooth hover behavior."""

    def __init__(self, target_widget: QWidget, on_enter: Callable[[], None], on_leave: Callable[[], None]):
        super().__init__(target_widget)
        self.target_widget = target_widget
        self.on_enter = on_enter
        self.on_leave = on_leave
        target_widget.installEventFilter(self)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched == self.target_widget:
            if event.type() == QEvent.Type.Enter:
                self.on_enter()
            elif event.type() == QEvent.Type.Leave:
                self.on_leave()
        return super().eventFilter(watched, event)


class ScaleAnimation(QObject):
    """Smooth geometry scaling animation for button presses and hover feedback."""

    def __init__(self, widget: QWidget, scale_factor: float = 0.96, duration: int = ANIM_FAST):
        super().__init__(widget)
        self.widget = widget
        self.scale_factor = scale_factor
        self.duration = duration
        self.original_geometry: Optional[QRect] = None

        self.anim = QPropertyAnimation(self.widget, b"geometry", self)
        self.anim.setDuration(self.duration)
        self.anim.setEasingCurve(EASING_SPRING)

    def scale_down(self):
        """Scales down the target widget around its center."""
        if not self.original_geometry:
            self.original_geometry = self.widget.geometry()

        rect = self.original_geometry
        new_w = int(rect.width() * self.scale_factor)
        new_h = int(rect.height() * self.scale_factor)
        dx = (rect.width() - new_w) // 2
        dy = (rect.height() - new_h) // 2

        scaled_rect = QRect(rect.x() + dx, rect.y() + dy, new_w, new_h)
        self.anim.stop()
        self.anim.setStartValue(self.widget.geometry())
        self.anim.setEndValue(scaled_rect)
        self.anim.start()

    def scale_restore(self):
        """Restores the target widget to its original size."""
        if not self.original_geometry:
            return

        self.anim.stop()
        self.anim.setStartValue(self.widget.geometry())
        self.anim.setEndValue(self.original_geometry)
        self.anim.start()

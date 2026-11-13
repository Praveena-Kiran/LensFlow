"""
Stop the mouse wheel from changing dropdowns, number boxes and sliders.

By default Qt lets the wheel change a dropdown's value whenever the
pointer is over it, so scrolling down a page silently changes settings.
With the guard installed on the application, scrolling over these
controls scrolls the page instead; values change only on purpose
(clicking the dropdown, dragging the slider, or the keyboard).
"""

from PySide6.QtCore import QCoreApplication, QEvent, QObject
from PySide6.QtWidgets import (
    QAbstractScrollArea,
    QAbstractSpinBox,
    QComboBox,
    QSlider,
)

GUARDED = (QComboBox, QAbstractSpinBox, QSlider)


class WheelGuard(QObject):

    def eventFilter(self, obj, event):
        if event.type() != QEvent.Type.Wheel or not isinstance(obj, GUARDED):
            return False

        # Hand the scroll to the page the control sits in, if any.
        parent = obj.parentWidget()
        while parent is not None and not isinstance(parent, QAbstractScrollArea):
            parent = parent.parentWidget()

        if parent is not None:
            bar = parent.verticalScrollBar()
            if bar is not None and bar.isVisible():
                QCoreApplication.sendEvent(bar, event)

        return True   # the control itself never sees the wheel


def install(app):
    """Install the guard on the whole application. Returns it (keep a reference)."""
    guard = WheelGuard(app)
    app.installEventFilter(guard)
    return guard

"""
Wield - Feedback overlay and controller

FeedbackOverlay: a small pill at the bottom of the screen that stays on
top of everything (including a full-screen PowerPoint slideshow), never
takes focus and lets clicks through. It shows what Wield just did:

    Wield is listening           (activated, stays while active)
    👍  →  Next slide            (action ran, fades after a moment)
    ⚠ Next slide didn't work     (error)

Feedback ties it to the sound cues and the user's settings, and only
shows the overlay when Wield's own window isn't the one in front (when
it is, the page's status line already says the same thing).
"""

from PySide6.QtCore import QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from backend.feedback.sounds import SoundCues
from backend.settings import gesture_settings

KIND_COLORS = {
    "info": "#60A5FA",
    "armed": "#34D399",
    "action": "#A78BFA",
    "error": "#F87171",
}

SHOW_MS = 1800
BOTTOM_MARGIN = 56


class FeedbackOverlay(QWidget):

    def __init__(self):
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
            | Qt.WindowType.WindowDoesNotAcceptFocus,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._fade_out)

        self._fade = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade.setDuration(250)
        self._fade.finished.connect(self._after_fade)

        self.kind = None

    def show_message(self, text, kind="info", sticky=False):
        """Show `text`. Sticky messages stay until replaced or cleared."""
        color = KIND_COLORS.get(kind, KIND_COLORS["info"])
        self.kind = kind
        self.label.setText(text)
        self.label.setStyleSheet(f"""
            QLabel {{
                background: rgba(17, 17, 24, 225);
                color: white;
                border: 2px solid {color};
                border-radius: 22px;
                padding: 10px 22px;
                font-size: 18px;
                font-weight: 600;
            }}
        """)
        self.adjustSize()
        self._place()

        self._fade.stop()
        self.setWindowOpacity(1.0)
        self.show()
        self.raise_()

        self._hide_timer.stop()
        if not sticky:
            self._hide_timer.start(SHOW_MS)

    def clear(self):
        self._hide_timer.stop()
        if self.isVisible():
            self._fade_out()

    def _place(self):
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        area = screen.availableGeometry()
        self.move(
            area.x() + (area.width() - self.width()) // 2,
            area.y() + area.height() - self.height() - BOTTOM_MARGIN,
        )

    def _fade_out(self):
        self._fade.stop()
        self._fade.setStartValue(self.windowOpacity())
        self._fade.setEndValue(0.0)
        self._fade.start()

    def _after_fade(self):
        if self.windowOpacity() <= 0.01:
            self.hide()
            self.kind = None


class Feedback:
    """Sound + overlay feedback, following the user's settings."""

    def __init__(self, main_window=None, overlay=None, sounds=None):
        self.main_window = main_window
        self.overlay = overlay or FeedbackOverlay()
        self.sounds = sounds or SoundCues()
        self.overlay_enabled = True
        self.reload()

    def reload(self):
        settings = gesture_settings.load()
        self.sounds.enabled = settings["sound_feedback"]
        self.overlay_enabled = settings["feedback_overlay"]
        if not self.overlay_enabled:
            self.overlay.clear()

    def _overlay(self, text, kind, sticky=False):
        if not self.overlay_enabled:
            return
        # Wield's own window already shows this in its status line.
        if self.main_window is not None and self.main_window.isActiveWindow():
            return
        self.overlay.show_message(text, kind, sticky)

    # ---------------------------------------------------------
    # Events
    # ---------------------------------------------------------

    def armed(self, trigger=""):
        self.reload()  # settings may have changed
        self.sounds.play("armed")
        self._overlay("Wield is listening", "armed", sticky=True)

    def disarmed(self):
        self.reload()  # settings may have changed
        self.sounds.play("disarmed")
        if self.overlay.kind == "armed":
            self.overlay.clear()

    def action(self, trigger, name):
        self.reload()  # settings may have changed
        self.sounds.play("action")
        self._overlay(f"{trigger}  →  {name}" if trigger else name, "action")

    def failed(self, name, message=""):
        self.reload()  # settings may have changed
        self.sounds.play("error")
        self._overlay(f"⚠ {name} didn't work", "error")

    def info(self, text, sticky=False):
        self.reload()  # settings may have changed
        self._overlay(text, "info", sticky)

    def stopped(self):
        self.overlay.clear()

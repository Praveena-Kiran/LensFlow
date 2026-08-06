"""LensFlow - Pulsing Interactive Glow Orb

Features:
- Idle breathing pulse animation
- Mouse hover expansion & glow enhancement
- Energetic listening pulse mode
- Gesture detection concentric ripple rings animation
- Interactive click feedback
"""

from typing import Optional
from PySide6.QtCore import (
    Qt, QRectF, QPointF, Property, QPropertyAnimation, QParallelAnimationGroup,
    QEasingCurve, QTimer, Signal
)
from PySide6.QtGui import (
    QPainter, QRadialGradient, QColor, QBrush, QFont, QPainterPath, QPen
)
from PySide6.QtWidgets import QWidget


class GlowOrb(QWidget):
    """Interactive animated orb featuring idle breathing, hover scaling, listening pulse, and gesture ripple effects."""

    gesture_detected = Signal()  # Emitted when a gesture ripple is triggered

    MODE_IDLE = "idle"
    MODE_LISTENING = "listening"

    def __init__(self, diameter: int = 130, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._diameter = diameter
        self.mode = self.MODE_IDLE
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Animated Properties
        self._glow_factor = 1.0
        self._hover_scale = 1.0
        self._ripple_factor = 0.0  # 0.0 (no ripple) to 1.0 (fully expanded ripple)

        total = diameter + 40
        self.setFixedSize(total, total)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # ── 1. Idle Breathing Animation ────────────────────────────────
        self._idle_anim = QPropertyAnimation(self, b"glow_factor", self)
        self._idle_anim.setDuration(3200)
        self._idle_anim.setKeyValueAt(0.0, 0.88)
        self._idle_anim.setKeyValueAt(0.5, 1.15)
        self._idle_anim.setKeyValueAt(1.0, 0.88)
        self._idle_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._idle_anim.setLoopCount(-1)
        self._idle_anim.start()

        # ── 2. Hover Expansion Animation ──────────────────────────────
        self._hover_anim = QPropertyAnimation(self, b"hover_scale", self)
        self._hover_anim.setDuration(220)
        self._hover_anim.setEasingCurve(QEasingCurve.Type.OutBack)

        # ── 3. Gesture Ripple Animation ───────────────────────────────
        self._ripple_anim = QPropertyAnimation(self, b"ripple_factor", self)
        self._ripple_anim.setDuration(900)
        self._ripple_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    # ── Animated Qt Properties ──────────────────────────────────────────

    def _get_glow(self) -> float:
        return self._glow_factor

    def _set_glow(self, v: float):
        self._glow_factor = v
        self.update()

    glow_factor = Property(float, _get_glow, _set_glow)

    def _get_hover_scale(self) -> float:
        return self._hover_scale

    def _set_hover_scale(self, v: float):
        self._hover_scale = v
        self.update()

    hover_scale = Property(float, _get_hover_scale, _set_hover_scale)

    def _get_ripple(self) -> float:
        return self._ripple_factor

    def _set_ripple(self, v: float):
        self._ripple_factor = v
        self.update()

    ripple_factor = Property(float, _get_ripple, _set_ripple)

    # ── Interactive Mode Controls ───────────────────────────────────────

    def set_mode(self, mode_name: str):
        """Switches between IDLE and LISTENING modes."""
        self.mode = mode_name
        if mode_name == self.MODE_LISTENING:
            self._idle_anim.setDuration(1200)  # Faster pulse during listening
            self._idle_anim.setKeyValueAt(0.5, 1.25)
        else:
            self._idle_anim.setDuration(3200)
            self._idle_anim.setKeyValueAt(0.5, 1.15)
        self.update()

    def toggle_listening(self) -> str:
        """Toggles between listening and idle states."""
        new_mode = self.MODE_LISTENING if self.mode == self.MODE_IDLE else self.MODE_IDLE
        self.set_mode(new_mode)
        return new_mode

    def trigger_ripple(self):
        """Triggers an expanding gesture detection ripple ring."""
        self._ripple_anim.stop()
        self._ripple_anim.setStartValue(0.0)
        self._ripple_anim.setEndValue(1.0)
        self._ripple_anim.start()
        self.gesture_detected.emit()

    # ── Mouse Events for Hover & Click ─────────────────────────────────

    def enterEvent(self, event):
        """Mouse hover enter -> smooth expansion."""
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_scale)
        self._hover_anim.setEndValue(1.10)  # Expand slightly on hover
        self._hover_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Mouse hover leave -> restore size."""
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_scale)
        self._hover_anim.setEndValue(1.0)
        self._hover_anim.start()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """Mouse click -> trigger gesture ripple feedback."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.trigger_ripple()
        super().mousePressEvent(event)

    # ── Paint Event ─────────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx, cy = self.width() / 2.0, self.height() / 2.0
        base_r = (self._diameter / 2.0) * self._hover_scale

        # ── 1. Gesture Ripple Rings ──────────────────────────────────────
        if self._ripple_factor > 0.001:
            rip_r1 = base_r * (1.0 + 1.2 * self._ripple_factor)
            rip_alpha = int(180 * (1.0 - self._ripple_factor))
            pen1 = QPen(QColor(96, 165, 250, rip_alpha), 2.5)
            p.setPen(pen1)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(cx, cy), rip_r1, rip_r1)

            rip_r2 = base_r * (1.0 + 0.7 * self._ripple_factor)
            rip_alpha2 = int(140 * (1.0 - self._ripple_factor))
            pen2 = QPen(QColor(139, 92, 246, rip_alpha2), 1.8)
            p.setPen(pen2)
            p.drawEllipse(QPointF(cx, cy), rip_r2, rip_r2)

        # ── 2. Outer Ambient Glow Halo ──────────────────────────────────
        glow_multiplier = 2.2 if self.mode == self.MODE_LISTENING else 1.9
        glow_r = base_r * glow_multiplier * self._glow_factor

        glow = QRadialGradient(QPointF(cx, cy), glow_r)
        if self.mode == self.MODE_LISTENING:
            glow.setColorAt(0.0, QColor(59, 130, 246, 90))
            glow.setColorAt(0.35, QColor(168, 85, 247, 55))
            glow.setColorAt(0.7, QColor(99, 102, 241, 20))
            glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        else:
            glow.setColorAt(0.0, QColor(59, 130, 246, 55))
            glow.setColorAt(0.35, QColor(139, 92, 246, 35))
            glow.setColorAt(0.7, QColor(99, 102, 241, 12))
            glow.setColorAt(1.0, QColor(0, 0, 0, 0))

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(glow))
        p.drawEllipse(QRectF(cx - glow_r, cy - glow_r, glow_r * 2, glow_r * 2))

        # ── 3. Inner Orb Body Gradient ───────────────────────────────────
        orb_grad = QRadialGradient(QPointF(cx - base_r * 0.2, cy - base_r * 0.25), base_r * 1.15)
        if self.mode == self.MODE_LISTENING:
            orb_grad.setColorAt(0.0, QColor(147, 197, 253))  # Electric bright highlight
            orb_grad.setColorAt(0.3, QColor(59, 130, 246))
            orb_grad.setColorAt(0.7, QColor(168, 85, 247))   # Purple wave
            orb_grad.setColorAt(1.0, QColor(79, 70, 229))
        else:
            orb_grad.setColorAt(0.0, QColor(110, 175, 255))
            orb_grad.setColorAt(0.3, QColor(59, 130, 246))
            orb_grad.setColorAt(0.7, QColor(99, 102, 241))
            orb_grad.setColorAt(1.0, QColor(67, 56, 202))

        p.setBrush(QBrush(orb_grad))
        p.drawEllipse(QRectF(cx - base_r, cy - base_r, base_r * 2, base_r * 2))

        # ── 4. Specular Curved Highlight ───────────────────────────────
        highlight = QPainterPath()
        hr = base_r * 0.5
        highlight.addEllipse(QRectF(cx - hr * 0.5, cy - base_r + base_r * 0.1, hr * 1.0, hr * 0.55))
        p.setBrush(QBrush(QColor(255, 255, 255, 32)))
        p.drawPath(highlight)

        # ── 5. Monogram "LF" Text ───────────────────────────────────────
        p.setPen(QColor(255, 255, 255, 230))
        font = QFont("Inter", int(base_r * 0.50))
        font.setWeight(QFont.Weight.Bold)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2.0)
        p.setFont(font)
        p.drawText(
            QRectF(cx - base_r, cy - base_r, base_r * 2, base_r * 2),
            Qt.AlignmentFlag.AlignCenter,
            "LF"
        )

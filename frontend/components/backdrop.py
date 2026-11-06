"""
The window background. Plain for Dark and Light; Galaxy paints a starfield
with soft nebulae, Jungle paints large, faint leaves in the corners. Drawn
once per size and cached, so it costs nothing while the app runs.
"""

import math
import random

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPixmap, QRadialGradient
from PySide6.QtWidgets import QWidget

from frontend.styles.theme import BACKDROP, BG_DARK, PRIMARY, SECONDARY_ACCENT


class BackdropWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cache = None
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def resizeEvent(self, event):
        self._cache = None
        super().resizeEvent(event)

    def paintEvent(self, event):

        if self._cache is None or self._cache.size() != self.size():
            self._cache = self._render()

        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._cache)
        painter.end()

    # -----------------------------------------------------

    def _render(self):

        pixmap = QPixmap(self.size())
        pixmap.fill(QColor(BG_DARK))

        if BACKDROP is None or self.width() <= 0:
            return pixmap

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if BACKDROP == "stars":
            self._paint_galaxy(painter)
        elif BACKDROP == "leaves":
            self._paint_jungle(painter)

        painter.end()
        return pixmap

    def _glow(self, painter, cx, cy, radius, color, alpha):
        gradient = QRadialGradient(QPointF(cx, cy), radius)
        c = QColor(color)
        c.setAlpha(alpha)
        gradient.setColorAt(0.0, c)
        c.setAlpha(0)
        gradient.setColorAt(1.0, c)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

    def _paint_galaxy(self, painter):

        w, h = self.width(), self.height()
        rng = random.Random(7)  # same sky every time

        # Two faint nebulae.
        self._glow(painter, w * 0.82, h * 0.18, max(w, h) * 0.38, PRIMARY, 34)
        self._glow(painter, w * 0.12, h * 0.88, max(w, h) * 0.32, SECONDARY_ACCENT, 22)

        # Stars: mostly tiny and dim, a few brighter ones.
        painter.setPen(Qt.PenStyle.NoPen)
        count = int(w * h / 5200)

        for _ in range(count):
            x, y = rng.random() * w, rng.random() * h
            bright = rng.random() < 0.06
            r = rng.uniform(0.9, 1.6) if bright else rng.uniform(0.4, 0.9)
            painter.setBrush(QColor(255, 255, 255, rng.randint(120, 210) if bright else rng.randint(35, 110)))
            painter.drawEllipse(QPointF(x, y), r, r)

    def _leaf(self, painter, cx, cy, length, angle, color, alpha):
        """A simple leaf: two curves meeting at the tip, with a midrib."""

        painter.save()
        painter.translate(cx, cy)
        painter.rotate(angle)

        width = length * 0.42
        path = QPainterPath(QPointF(0, 0))
        path.cubicTo(QPointF(length * 0.25, -width), QPointF(length * 0.75, -width * 0.8), QPointF(length, 0))
        path.cubicTo(QPointF(length * 0.75, width * 0.8), QPointF(length * 0.25, width), QPointF(0, 0))

        c = QColor(color)
        c.setAlpha(alpha)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(c)
        painter.drawPath(path)

        rib = QColor(BG_DARK)
        rib.setAlpha(min(255, alpha * 2))
        painter.setPen(rib)
        painter.drawLine(QPointF(length * 0.05, 0), QPointF(length * 0.92, 0))

        painter.restore()

    def _paint_jungle(self, painter):

        w, h = self.width(), self.height()
        s = max(w, h)

        self._glow(painter, w * 0.15, h * 0.05, s * 0.45, PRIMARY, 18)
        self._glow(painter, w * 0.9, h * 0.95, s * 0.4, SECONDARY_ACCENT, 12)

        leaf = "#2E7D57"

        # Top-left cluster, hanging down into the window.
        for angle, length, alpha in ((60, 0.30, 46), (35, 0.26, 38), (85, 0.24, 34), (15, 0.20, 30)):
            self._leaf(painter, -s * 0.02, -s * 0.02, s * length, angle, leaf, alpha)

        # Bottom-right cluster, reaching up.
        for angle, length, alpha in ((-120, 0.30, 44), (-150, 0.24, 36), (-95, 0.22, 32)):
            self._leaf(painter, w + s * 0.02, h + s * 0.02, s * length, angle, leaf, alpha)

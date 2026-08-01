"""LensFlow Design System - Vector Outline Icon Renderer

Provides high-DPI resolution outline vector icons drawn using QPainter.
"""

from typing import Optional
from PySide6.QtCore import Qt, QSize, QRectF, QPointF
from PySide6.QtGui import QPainter, QPainterPath, QPen, QColor
from PySide6.QtWidgets import QWidget
from frontend.ui.styles.colors import TEXT_SECONDARY, get_qcolor


class VectorIcon(QWidget):
    """Clean outline vector icon widget drawn using anti-aliased QPainter paths."""

    # Icon Types
    SEARCH = "search"
    DRAG_HANDLE = "drag_handle"
    STUDIO = "studio"
    APP = "app"
    GESTURE = "gesture"
    WORKFLOW = "workflow"
    TOGGLE = "toggle"
    SIDEBAR_TOGGLE = "sidebar_toggle"
    CHEVRON_RIGHT = "chevron_right"
    PLUS = "plus"
    GRID = "grid"
    SETTINGS = "settings"
    COLOR_SWATCH = "color_swatch"
    HOME = "home"
    HISTORY = "history"

    def __init__(
        self,
        icon_type: str = SEARCH,
        color: str = TEXT_SECONDARY,
        size: int = 20,
        stroke_width: float = 1.8,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.icon_type = icon_type
        self.color_str = color
        self.stroke_width = stroke_width
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def set_color(self, color_str: str):
        """Updates icon color and triggers repaint."""
        self.color_str = color_str
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        color = get_qcolor(self.color_str)
        pen = QPen(color, self.stroke_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)

        w, h = float(self.width()), float(self.height())
        pad = self.stroke_width + 1.0
        rect = QRectF(pad, pad, w - 2 * pad, h - 2 * pad)

        path = QPainterPath()

        if self.icon_type == self.SEARCH:
            # Magnifying glass circle & handle
            cx, cy = rect.x() + rect.width() * 0.42, rect.y() + rect.height() * 0.42
            r = min(rect.width(), rect.height()) * 0.35
            path.addEllipse(QPointF(cx, cy), r, r)
            hx1 = cx + r * 0.707
            hy1 = cy + r * 0.707
            hx2 = rect.right()
            hy2 = rect.bottom()
            path.moveTo(hx1, hy1)
            path.lineTo(hx2, hy2)

        elif self.icon_type == self.DRAG_HANDLE:
            # 6-dot grip handle grid
            col1 = rect.x() + rect.width() * 0.35
            col2 = rect.x() + rect.width() * 0.65
            rows = [rect.y() + rect.height() * 0.2, rect.y() + rect.height() * 0.5, rect.y() + rect.height() * 0.8]
            dot_r = 1.2
            painter.setBrush(color)
            for r_y in rows:
                painter.drawEllipse(QPointF(col1, r_y), dot_r, dot_r)
                painter.drawEllipse(QPointF(col2, r_y), dot_r, dot_r)
            return

        elif self.icon_type == self.STUDIO:
            # Magic wand / Studio sparkle
            path.moveTo(rect.left(), rect.bottom())
            path.lineTo(rect.right() - rect.width() * 0.3, rect.top() + rect.height() * 0.3)
            # Sparkle star top right
            cx, cy = rect.right() - rect.width() * 0.15, rect.top() + rect.height() * 0.15
            sp = rect.width() * 0.12
            path.moveTo(cx - sp, cy); path.lineTo(cx + sp, cy)
            path.moveTo(cx, cy - sp); path.lineTo(cx, cy + sp)

        elif self.icon_type == self.APP:
            # Modern app rounded square tile
            path.addRoundedRect(rect, rect.width() * 0.25, rect.height() * 0.25)
            inner_r = QRectF(rect.x() + rect.width() * 0.28, rect.y() + rect.height() * 0.28, rect.width() * 0.44, rect.height() * 0.44)
            path.addRoundedRect(inner_r, inner_r.width() * 0.2, inner_r.height() * 0.2)

        elif self.icon_type == self.GESTURE:
            # Hand gesture icon
            path.moveTo(rect.x() + rect.width() * 0.3, rect.bottom())
            path.lineTo(rect.x() + rect.width() * 0.3, rect.top() + rect.height() * 0.3)
            path.arcTo(QRectF(rect.x() + rect.width() * 0.3, rect.top(), rect.width() * 0.4, rect.height() * 0.4), 180, -180)
            path.lineTo(rect.x() + rect.width() * 0.7, rect.bottom())

        elif self.icon_type == self.WORKFLOW:
            # Connected workflow nodes
            path.addEllipse(QPointF(rect.left() + rect.width() * 0.2, rect.top() + rect.height() * 0.5), rect.width() * 0.18, rect.height() * 0.18)
            path.addEllipse(QPointF(rect.right() - rect.width() * 0.2, rect.top() + rect.height() * 0.25), rect.width() * 0.18, rect.height() * 0.18)
            path.addEllipse(QPointF(rect.right() - rect.width() * 0.2, rect.bottom() - rect.height() * 0.25), rect.width() * 0.18, rect.height() * 0.18)
            path.moveTo(rect.left() + rect.width() * 0.38, rect.top() + rect.height() * 0.45)
            path.lineTo(rect.right() - rect.width() * 0.38, rect.top() + rect.height() * 0.28)
            path.moveTo(rect.left() + rect.width() * 0.38, rect.top() + rect.height() * 0.55)
            path.lineTo(rect.right() - rect.width() * 0.38, rect.bottom() - rect.height() * 0.28)

        elif self.icon_type == self.SIDEBAR_TOGGLE:
            # Panel sidebar toggle icon
            path.addRoundedRect(rect, 4, 4)
            path.moveTo(rect.left() + rect.width() * 0.35, rect.top())
            path.lineTo(rect.left() + rect.width() * 0.35, rect.bottom())

        elif self.icon_type == self.GRID:
            # 4-square grid
            hw = rect.width() * 0.4
            path.addRoundedRect(QRectF(rect.left(), rect.top(), hw, hw), 2, 2)
            path.addRoundedRect(QRectF(rect.right() - hw, rect.top(), hw, hw), 2, 2)
            path.addRoundedRect(QRectF(rect.left(), rect.bottom() - hw, hw, hw), 2, 2)
            path.addRoundedRect(QRectF(rect.right() - hw, rect.bottom() - hw, hw, hw), 2, 2)

        elif self.icon_type == self.PLUS:
            # Plus icon
            path.moveTo(rect.center().x(), rect.top())
            path.lineTo(rect.center().x(), rect.bottom())
            path.moveTo(rect.left(), rect.center().y())
            path.lineTo(rect.right(), rect.center().y())

        elif self.icon_type == self.HOME:
            # House icon — roof triangle + body rectangle
            cx = rect.x() + rect.width() / 2.0
            # Roof
            path.moveTo(rect.left(), rect.top() + rect.height() * 0.45)
            path.lineTo(cx, rect.top())
            path.lineTo(rect.right(), rect.top() + rect.height() * 0.45)
            # Body
            body_top = rect.top() + rect.height() * 0.45
            path.moveTo(rect.left() + rect.width() * 0.12, body_top)
            path.lineTo(rect.left() + rect.width() * 0.12, rect.bottom())
            path.lineTo(rect.right() - rect.width() * 0.12, rect.bottom())
            path.lineTo(rect.right() - rect.width() * 0.12, body_top)

        elif self.icon_type == self.HISTORY:
            # Clock icon — circle + hour/minute hands
            cx, cy = rect.center().x(), rect.center().y()
            r = min(rect.width(), rect.height()) * 0.48
            path.addEllipse(QPointF(cx, cy), r, r)
            path.moveTo(cx, cy)
            path.lineTo(cx, cy - r * 0.55)
            path.moveTo(cx, cy)
            path.lineTo(cx + r * 0.4, cy + r * 0.15)

        elif self.icon_type == self.SETTINGS:
            # Gear icon — outer circle with notches + inner circle
            cx, cy = rect.center().x(), rect.center().y()
            outer_r = min(rect.width(), rect.height()) * 0.48
            inner_r = outer_r * 0.42
            path.addEllipse(QPointF(cx, cy), outer_r, outer_r)
            path.addEllipse(QPointF(cx, cy), inner_r, inner_r)
            # Cross-hair notches
            import math
            for angle_deg in range(0, 360, 45):
                a = math.radians(angle_deg)
                x1 = cx + outer_r * 0.75 * math.cos(a)
                y1 = cy + outer_r * 0.75 * math.sin(a)
                x2 = cx + (outer_r + self.stroke_width * 1.5) * math.cos(a)
                y2 = cy + (outer_r + self.stroke_width * 1.5) * math.sin(a)
                path.moveTo(x1, y1)
                path.lineTo(x2, y2)

        else:  # Fallback default circle
            path.addEllipse(rect)

        painter.drawPath(path)

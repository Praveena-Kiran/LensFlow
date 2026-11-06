"""LensFlow navigation sidebar.

Line icons are drawn in code (no image files or emoji), so they take the
theme's colours. Items: Home, Studios, Notifications (with a count badge),
History, Settings; the user's name at the bottom opens Settings.
"""

from typing import Dict, Optional

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from frontend.styles.theme import (
    BORDER,
    ON_PRIMARY,
    OVERLAY_1,
    PAGE_BG,
    PRIMARY,
    PRIMARY_MUTED,
    PRIMARY_TEXT,
    SECONDARY_TEXT,
    SURFACE_HOVER,
    TEXT_MUTED,
)
from backend.settings.user import display_name, initials


# ────────────────────────────────────────────────────────────────────────────
#  Icons
# ────────────────────────────────────────────────────────────────────────────

class _Icon(QWidget):
    """A 20px line icon drawn with QPainter."""

    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        self.name = name
        self.color = QColor(TEXT_MUTED)
        self.setFixedSize(20, 20)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def set_color(self, color):
        self.color = QColor(color)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(self.color, 1.6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        getattr(self, f"_draw_{self.name}", self._draw_dot)(p)
        p.end()

    def _draw_home(self, p):
        path = QPainterPath(QPointF(3.5, 9.5))
        path.lineTo(10, 4)
        path.lineTo(16.5, 9.5)
        path.lineTo(16.5, 16.5)
        path.lineTo(12, 16.5)
        path.lineTo(12, 12)
        path.lineTo(8, 12)
        path.lineTo(8, 16.5)
        path.lineTo(3.5, 16.5)
        path.closeSubpath()
        p.drawPath(path)

    def _draw_studios(self, p):
        for x, y in ((3.5, 3.5), (11, 3.5), (3.5, 11), (11, 11)):
            p.drawRoundedRect(QRectF(x, y, 5.5, 5.5), 1.6, 1.6)

    def _draw_bell(self, p):
        path = QPainterPath(QPointF(5, 14))
        path.lineTo(5, 9)
        path.cubicTo(QPointF(5, 5.5), QPointF(7.5, 3.5), QPointF(10, 3.5))
        path.cubicTo(QPointF(12.5, 3.5), QPointF(15, 5.5), QPointF(15, 9))
        path.lineTo(15, 14)
        path.lineTo(16.5, 15)
        path.lineTo(3.5, 15)
        path.closeSubpath()
        p.drawPath(path)
        p.drawLine(QPointF(8.5, 17), QPointF(11.5, 17))

    def _draw_history(self, p):
        p.drawEllipse(QRectF(3.5, 3.5, 13, 13))
        p.drawLine(QPointF(10, 6.5), QPointF(10, 10))
        p.drawLine(QPointF(10, 10), QPointF(12.5, 12))

    def _draw_settings(self, p):
        p.drawEllipse(QRectF(7.5, 7.5, 5, 5))
        for i in range(8):
            p.save()
            p.translate(10, 10)
            p.rotate(i * 45)
            p.drawLine(QPointF(0, -5.2), QPointF(0, -7))
            p.restore()
        p.drawEllipse(QRectF(5, 5, 10, 10))

    def _draw_dot(self, p):
        p.drawEllipse(QRectF(8, 8, 4, 4))


# ────────────────────────────────────────────────────────────────────────────
#  Menu item
# ────────────────────────────────────────────────────────────────────────────

class _NavItem(QPushButton):

    def __init__(self, item_id: str, label: str, icon: str, parent=None):
        super().__init__(parent)
        self.item_id = item_id
        self.is_active = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(40)
        self.setAccessibleName(label)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 10, 0)
        layout.setSpacing(12)

        self._icon = _Icon(icon)
        layout.addWidget(self._icon, 0, Qt.AlignmentFlag.AlignVCenter)

        self._label = QLabel(label)
        layout.addWidget(self._label, 1, Qt.AlignmentFlag.AlignVCenter)

        self._badge = QLabel("")
        self._badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._badge.setStyleSheet(f"""
            background: {PRIMARY}; color: {ON_PRIMARY}; border-radius: 9px;
            font-size: 11px; font-weight: 700; padding: 0 6px; min-width: 6px;
        """)
        self._badge.setFixedHeight(18)
        self._badge.hide()
        layout.addWidget(self._badge, 0, Qt.AlignmentFlag.AlignVCenter)

        self._update_style()

    def set_active(self, active: bool):
        self.is_active = active
        self._update_style()

    def set_badge(self, count: int):
        self._badge.setText(str(count))
        self._badge.setVisible(count > 0)
        name = self._label.text()
        self.setAccessibleName(f"{name}, {count} new" if count else name)

    def _update_style(self):
        active = self.is_active
        self.setStyleSheet(f"""
            _NavItem {{
                background-color: {PRIMARY_MUTED if active else 'transparent'};
                border: none; border-radius: 10px; text-align: left;
            }}
            _NavItem:hover {{ background-color: {PRIMARY_MUTED if active else OVERLAY_1}; }}
        """)
        self._label.setStyleSheet(
            f"color: {PRIMARY_TEXT if active else SECONDARY_TEXT}; font-size: 13px; "
            f"font-weight: {600 if active else 400}; border: none; background: transparent;"
        )
        self._icon.set_color(PRIMARY if active else TEXT_MUTED)


# ────────────────────────────────────────────────────────────────────────────
#  Avatar
# ────────────────────────────────────────────────────────────────────────────

class _AvatarBadge(QWidget):

    def __init__(self, text: str = "?", size: int = 30, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._text = text

    def set_text(self, text):
        self._text = text
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = float(min(self.width(), self.height()))
        p.setPen(QPen(QColor(BORDER), 1.0))
        p.setBrush(QColor(SURFACE_HOVER))
        p.drawEllipse(QRectF(0.5, 0.5, s - 1, s - 1))
        p.setPen(QColor(PRIMARY_TEXT))
        font = QFont("Inter", int(s * 0.32))
        font.setWeight(QFont.Weight.Bold)
        p.setFont(font)
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._text)


# ────────────────────────────────────────────────────────────────────────────
#  Sidebar
# ────────────────────────────────────────────────────────────────────────────

class AppSidebar(QFrame):

    item_selected = Signal(str)

    ITEMS = [
        ("home", "Home", "home"),
        ("studios", "Studios", "studios"),
        ("notifications", "Notifications", "bell"),
        ("history", "History", "history"),
        ("settings", "Settings", "settings"),
    ]

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("AppSidebar")
        self.setFixedWidth(208)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            QFrame#AppSidebar {{
                background-color: {PAGE_BG};
                border-right: 1px solid {BORDER};
            }}
        """)

        self._items: Dict[str, _NavItem] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(4)

        for item_id, label, icon in self.ITEMS:
            item = _NavItem(item_id, label, icon)
            item.clicked.connect(lambda _=False, iid=item_id: self._on_click(iid))
            self._items[item_id] = item
            layout.addWidget(item)

        layout.addStretch()

        # The user, at the bottom; opens Settings (where the name is set).
        profile = QPushButton()
        profile.setCursor(Qt.CursorShape.PointingHandCursor)
        profile.setFixedHeight(46)
        profile.setAccessibleName("Your profile and settings")
        profile.setStyleSheet(f"""
            QPushButton {{ background: transparent; border: none; border-radius: 10px; }}
            QPushButton:hover {{ background: {OVERLAY_1}; }}
        """)
        profile.clicked.connect(lambda: self._on_click("settings"))

        prof_layout = QHBoxLayout(profile)
        prof_layout.setContentsMargins(8, 0, 8, 0)
        prof_layout.setSpacing(10)

        self._avatar = _AvatarBadge()
        prof_layout.addWidget(self._avatar, 0, Qt.AlignmentFlag.AlignVCenter)

        self._name = QLabel("")
        self._name.setStyleSheet(
            f"color: {PRIMARY_TEXT}; font-size: 13px; font-weight: 500; border: none; background: transparent;"
        )
        prof_layout.addWidget(self._name, 1, Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(profile)

        self.refresh_user()
        self.set_active("home")

    def refresh_user(self):
        name = display_name()
        self._name.setText(name or "You")
        self._avatar.set_text(initials(name) if name else "?")

    def set_badge(self, item_id: str, count: int):
        if item_id in self._items:
            self._items[item_id].set_badge(count)

    def _on_click(self, item_id: str):
        self.set_active(item_id)
        self.item_selected.emit(item_id)

    def set_active(self, item_id: str):
        """Highlight an item without emitting item_selected."""
        for iid, item in self._items.items():
            item.set_active(iid == item_id)

"""LensFlow - Navigation Sidebar

Reusable sidebar with dynamic menu items, active state highlighting,
and a user profile section at the bottom.
"""

from typing import Optional, Dict, Callable
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QPainter, QColor, QFont, QBrush
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget
)


# ────────────────────────────────────────────────────────────────────────────
#  Sidebar Menu Item
# ────────────────────────────────────────────────────────────────────────────

class _NavItem(QPushButton):
    """Single navigation button with icon placeholder and label."""

    def __init__(self, item_id: str, label: str, parent=None):
        super().__init__(parent)
        self.item_id = item_id
        self.is_active = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(42)
        self.setCheckable(True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(14)

        # Icon placeholder (small dot when inactive, filled when active)
        self._dot = QWidget()
        self._dot.setFixedSize(20, 20)
        layout.addWidget(self._dot, 0, Qt.AlignmentFlag.AlignVCenter)

        self._label = QLabel(label)
        layout.addWidget(self._label, 1, Qt.AlignmentFlag.AlignVCenter)

        self._update_style()

    def set_active(self, active: bool):
        self.is_active = active
        self.setChecked(active)
        self._update_style()

    def _update_style(self):
        if self.is_active:
            bg = "rgba(59, 130, 246, 0.12)"
            text_color = "#FFFFFF"
            font_weight = "600"
            dot_bg = "#3B82F6"
        else:
            bg = "transparent"
            text_color = "#9CA3AF"
            font_weight = "400"
            dot_bg = "transparent"

        self.setStyleSheet(f"""
            _NavItem {{
                background-color: {bg};
                border: none;
                border-radius: 10px;
                text-align: left;
            }}
            _NavItem:hover {{
                background-color: rgba(255, 255, 255, 0.05);
            }}
        """)
        self._label.setStyleSheet(
            f"color: {text_color}; font-size: 14px; font-weight: {font_weight};"
        )
        self._dot.setStyleSheet(
            f"background-color: {dot_bg}; border-radius: 4px;"
        )


# ────────────────────────────────────────────────────────────────────────────
#  User Avatar Badge
# ────────────────────────────────────────────────────────────────────────────

class _AvatarBadge(QWidget):
    """Circular avatar badge with initials."""

    def __init__(self, initials: str = "PK", size: int = 34, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._initials = initials

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = float(min(self.width(), self.height()))

        # Circle background
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor("#27272A")))
        p.drawEllipse(QRectF(0, 0, s, s))

        # Border
        from PySide6.QtGui import QPen
        p.setPen(QPen(QColor(255, 255, 255, 20), 1.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(0.5, 0.5, s - 1, s - 1))

        # Initials
        p.setPen(QColor("#D1D5DB"))
        font = QFont("Inter", int(s * 0.28))
        font.setWeight(QFont.Weight.DemiBold)
        p.setFont(font)
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._initials)


# ────────────────────────────────────────────────────────────────────────────
#  Sidebar Widget
# ────────────────────────────────────────────────────────────────────────────

class AppSidebar(QFrame):
    """Reusable navigation sidebar with menu items and user profile."""

    item_selected = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("AppSidebar")
        self.setFixedWidth(200)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("""
            QFrame#AppSidebar {
                background-color: #0B0B0F;
                border-right: 1px solid rgba(255, 255, 255, 0.06);
            }
        """)

        self._items: Dict[str, _NavItem] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 12, 10, 16)
        layout.setSpacing(4)

        # ── Navigation Items ────────────────────────────────────────────
        self._items_layout = QVBoxLayout()
        self._items_layout.setSpacing(4)

        nav_items = [
            ("home", "Home"),
            ("studios", "Studios"),
            ("history", "History"),
            ("settings", "Settings"),
        ]

        for item_id, label in nav_items:
            item = _NavItem(item_id, label)
            item.clicked.connect(lambda _, iid=item_id: self._on_click(iid))
            self._items[item_id] = item
            self._items_layout.addWidget(item)

        layout.addLayout(self._items_layout)
        layout.addStretch()

        # ── User Profile ────────────────────────────────────────────────
        profile = QPushButton()
        profile.setCursor(Qt.CursorShape.PointingHandCursor)
        profile.setFixedHeight(46)
        profile.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.04);
            }
        """)

        prof_layout = QHBoxLayout(profile)
        prof_layout.setContentsMargins(8, 0, 8, 0)
        prof_layout.setSpacing(10)

        avatar = _AvatarBadge("PK", size=32)
        prof_layout.addWidget(avatar, 0, Qt.AlignmentFlag.AlignVCenter)

        name = QLabel("Praveena K.")
        name.setStyleSheet("color: #D1D5DB; font-size: 13px; font-weight: 500;")
        prof_layout.addWidget(name, 1, Qt.AlignmentFlag.AlignVCenter)

        chevron = QLabel("\u2304")
        chevron.setStyleSheet("color: #6B7280; font-size: 16px;")
        prof_layout.addWidget(chevron, 0, Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(profile)

        # Default selection
        self._on_click("home")

    def _on_click(self, item_id: str):
        for iid, item in self._items.items():
            item.set_active(iid == item_id)
        self.item_selected.emit(item_id)

    def select(self, item_id: str):
        """Programmatically select a sidebar item."""
        self._on_click(item_id)

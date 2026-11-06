"""LensFlow - Navigation Sidebar

Reusable sidebar with dynamic menu items, active state highlighting,
and a user profile section at the bottom.
"""

from typing import Optional, Dict
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QPainter, QColor, QFont, QBrush, QPen
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget
)

from frontend.styles.theme import (
    BG_DARK,
    SURFACE_HOVER,
    BORDER,
    PRIMARY_TEXT,
    SECONDARY_TEXT,
    TEXT_MUTED,
    PRIMARY,
    PRIMARY_MUTED,
)


# ────────────────────────────────────────────────────────────────────────────
#  Sidebar Menu Item
# ────────────────────────────────────────────────────────────────────────────

class _NavItem(QPushButton):
    """Navigation button with icon indicator and label."""

    def __init__(self, item_id: str, label: str, icon_str: str = "•", parent=None):
        super().__init__(parent)
        self.item_id = item_id
        self.is_active = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(38)
        self.setCheckable(True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(12)

        self._icon_label = QLabel(icon_str)
        self._icon_label.setFixedWidth(16)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._icon_label, 0, Qt.AlignmentFlag.AlignVCenter)

        self._label = QLabel(label)
        layout.addWidget(self._label, 1, Qt.AlignmentFlag.AlignVCenter)

        self._update_style()

    def set_active(self, active: bool):
        self.is_active = active
        self.setChecked(active)
        self._update_style()

    def _update_style(self):
        if self.is_active:
            bg = PRIMARY_MUTED
            text_color = PRIMARY_TEXT
            font_weight = "600"
            icon_color = PRIMARY
            border_css = "border: 1px solid rgba(124, 92, 255, 0.25);"
        else:
            bg = "transparent"
            text_color = SECONDARY_TEXT
            font_weight = "400"
            icon_color = TEXT_MUTED
            border_css = "border: 1px solid transparent;"

        self.setStyleSheet(f"""
            _NavItem {{
                background-color: {bg};
                {border_css}
                border-radius: 8px;
                text-align: left;
            }}
            _NavItem:hover {{
                background-color: rgba(255, 255, 255, 0.05);
                color: #FFFFFF;
            }}
        """)
        self._label.setStyleSheet(
            f"color: {text_color}; font-size: 13px; font-weight: {font_weight}; border: none; background: transparent;"
        )
        self._icon_label.setStyleSheet(
            f"color: {icon_color}; font-size: 13px; font-weight: 600; border: none; background: transparent;"
        )


# ────────────────────────────────────────────────────────────────────────────
#  User Avatar Badge
# ────────────────────────────────────────────────────────────────────────────

class _AvatarBadge(QWidget):
    """Circular avatar badge with initials and subtle border."""

    def __init__(self, initials: str = "PK", size: int = 32, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._initials = initials

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = float(min(self.width(), self.height()))

        # Circle background
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor("#171923")))
        p.drawEllipse(QRectF(0, 0, s, s))

        # Border
        p.setPen(QPen(QColor(BORDER), 1.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(0.5, 0.5, s - 1.0, s - 1.0))

        # Initials
        p.setPen(QColor(PRIMARY_TEXT))
        font = QFont("Inter", int(s * 0.32))
        font.setWeight(QFont.Weight.Bold)
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
        self.setStyleSheet(f"""
            QFrame#AppSidebar {{
                background-color: {BG_DARK};
                border-right: 1px solid {BORDER};
            }}
        """)

        self._items: Dict[str, _NavItem] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 14, 10, 16)
        layout.setSpacing(4)

        # ── Navigation Items ────────────────────────────────────────────
        self._items_layout = QVBoxLayout()
        self._items_layout.setSpacing(4)

        nav_items = [
            ("home", "Home", "⌂"),
            ("studios", "Studios", "▦"),
            ("history", "History", "⏱"),
            ("settings", "Settings", "⚙"),
        ]

        for item_id, label, icon in nav_items:
            item = _NavItem(item_id, label, icon)
            item.clicked.connect(lambda _, iid=item_id: self._on_click(iid))
            self._items[item_id] = item
            self._items_layout.addWidget(item)

        layout.addLayout(self._items_layout)
        layout.addStretch()

        # ── User Profile ────────────────────────────────────────────────
        profile = QPushButton()
        profile.setCursor(Qt.CursorShape.PointingHandCursor)
        profile.setFixedHeight(44)
        profile.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid transparent;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid {BORDER};
            }}
        """)

        prof_layout = QHBoxLayout(profile)
        prof_layout.setContentsMargins(8, 0, 8, 0)
        prof_layout.setSpacing(10)

        avatar = _AvatarBadge("PK", size=30)
        prof_layout.addWidget(avatar, 0, Qt.AlignmentFlag.AlignVCenter)

        name = QLabel("Praveena K.")
        name.setStyleSheet(f"color: {PRIMARY_TEXT}; font-size: 13px; font-weight: 500; border: none; background: transparent;")
        prof_layout.addWidget(name, 1, Qt.AlignmentFlag.AlignVCenter)

        chevron = QLabel("⌵")
        chevron.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px; border: none; background: transparent;")
        prof_layout.addWidget(chevron, 0, Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(profile)

        # Default selection
        self._on_click("home")

    def _on_click(self, item_id: str):
        self.set_active(item_id)
        self.item_selected.emit(item_id)

    def set_active(self, item_id: str):
        """Highlight an item without emitting item_selected."""
        for iid, item in self._items.items():
            item.set_active(iid == item_id)

    def select(self, item_id: str):
        """Programmatically select a sidebar item."""
        self._on_click(item_id)

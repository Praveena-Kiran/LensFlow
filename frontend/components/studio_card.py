"""LensFlow - Reusable Studio Card

Compact card displaying studio icon badge, title, time-ago, description,
app chips, last-used timestamp, and accent-coloured Launch button.
"""

from typing import Optional
from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import (
    QPainter, QColor, QFont, QRadialGradient, QBrush
)
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QSizePolicy, QGraphicsDropShadowEffect
)


class _IconBadge(QWidget):
    """Circular coloured badge with a centred symbol drawn via QPainter."""

    def __init__(self, symbol: str, color: str, size: int = 40, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._symbol = symbol
        self._color = QColor(color)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = float(min(self.width(), self.height()))

        # Filled circle
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(self._color.darker(130)))
        p.drawEllipse(QRectF(0, 0, s, s))

        # Inner lighter circle
        pad = s * 0.06
        inner = QRectF(pad, pad, s - 2 * pad, s - 2 * pad)
        grad = QRadialGradient(inner.center(), s * 0.45)
        grad.setColorAt(0.0, self._color.lighter(120))
        grad.setColorAt(1.0, self._color)
        p.setBrush(QBrush(grad))
        p.drawEllipse(inner)

        # Symbol text
        p.setPen(QColor(255, 255, 255, 230))
        font = QFont("Inter", int(s * 0.26))
        font.setWeight(QFont.Weight.Bold)
        p.setFont(font)
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._symbol)


class StudioCard(QFrame):
    """Reusable compact studio card widget matching the LensFlow design language."""

    launch_clicked = Signal(str)

    def __init__(
        self,
        title: str,
        time_ago: str,
        description: str,
        apps: list,
        last_used: str,
        icon_symbol: str = "LF",
        accent: str = "#3B82F6",
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._title = title
        self._accent = accent
        self.setObjectName("StudioCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(225)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(shadow)

        self._apply_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)

        # ── Row 1: Icon + Title + Time Ago ──────────────────────────────
        top = QHBoxLayout()
        top.setSpacing(12)

        badge = _IconBadge(icon_symbol, accent, size=38)
        top.addWidget(badge, 0, Qt.AlignmentFlag.AlignTop)

        title_col = QVBoxLayout()
        title_col.setSpacing(4)

        t = QLabel(title)
        t.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 600; letter-spacing: -0.1px;")
        title_col.addWidget(t)

        desc = QLabel(description)
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #9CA3AF; font-size: 12px; font-weight: 400; line-height: 1.4;")
        title_col.addWidget(desc)

        top.addLayout(title_col, 1)

        time_lbl = QLabel(time_ago)
        time_lbl.setStyleSheet("color: #6B7280; font-size: 11px; font-weight: 400;")
        top.addWidget(time_lbl, 0, Qt.AlignmentFlag.AlignTop)

        layout.addLayout(top)
        layout.addSpacing(12)

        # ── Row 2: App Chips ────────────────────────────────────────────
        chips_row = QHBoxLayout()
        chips_row.setSpacing(6)
        chips_row.setContentsMargins(0, 0, 0, 0)

        for name in apps[:4]:
            chip = QLabel(name)
            chip.setStyleSheet("""
                color: #D1D5DB;
                background-color: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 8px;
                font-size: 11px;
                font-weight: 500;
                padding: 3px 10px;
            """)
            chip.setFixedHeight(24)
            chips_row.addWidget(chip)
        chips_row.addStretch()

        layout.addLayout(chips_row)
        layout.addStretch()

        # ── Row 3: Last Used + Launch Button ────────────────────────────
        bottom = QHBoxLayout()
        bottom.setContentsMargins(0, 0, 0, 0)

        used_col = QVBoxLayout()
        used_col.setSpacing(1)
        used_label = QLabel("Last used")
        used_label.setStyleSheet("color: #6B7280; font-size: 10px; font-weight: 400;")
        used_col.addWidget(used_label)

        used_val = QLabel(last_used)
        used_val.setStyleSheet("color: #9CA3AF; font-size: 11px; font-weight: 500;")
        used_col.addWidget(used_val)

        bottom.addLayout(used_col)
        bottom.addStretch()

        launch = QPushButton("Launch  \u2192")
        launch.setCursor(Qt.CursorShape.PointingHandCursor)
        launch.setFixedSize(100, 34)
        launch.setStyleSheet(f"""
            QPushButton {{
                background-color: {accent};
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {QColor(accent).lighter(120).name()};
            }}
            QPushButton:pressed {{
                background-color: {QColor(accent).darker(120).name()};
            }}
        """)
        launch.clicked.connect(lambda: self.launch_clicked.emit(self._title))
        bottom.addWidget(launch, 0, Qt.AlignmentFlag.AlignBottom)

        layout.addLayout(bottom)

    def _apply_style(self):
        self.setStyleSheet(f"""
            QFrame#StudioCard {{
                background-color: #16161E;
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 16px;
            }}
            QFrame#StudioCard:hover {{
                border: 1px solid rgba(59, 130, 246, 0.3);
                background-color: #1A1A24;
            }}
        """)

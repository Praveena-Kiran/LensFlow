"""LensFlow - Custom Window Title Bar Controls

Frameless custom title bar providing LensFlow brand identity, window dragging,
and Windows 11 style Minimize, Maximize/Restore, and Close buttons.
"""

from typing import Optional
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QRadialGradient, QBrush
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QGraphicsDropShadowEffect
)


class WindowControlButton(QPushButton):
    """Minimal window control button (Minimize, Maximize, Close)."""

    def __init__(self, symbol: str, tooltip: str = "", is_close: bool = False, parent=None):
        super().__init__(symbol, parent)
        self.setFixedSize(46, 36)
        self.setToolTip(tooltip)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.is_close = is_close
        self._apply_style()

    def set_symbol(self, symbol: str):
        self.setText(symbol)

    def _apply_style(self):
        hover_bg = "#EF4444" if self.is_close else "rgba(255, 255, 255, 0.12)"
        hover_fg = "#FFFFFF"

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: #9CA3AF;
                border: none;
                font-size: 13px;
                font-weight: 500;
                font-family: "Segoe UI", "Inter", sans-serif;
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
                color: {hover_fg};
            }}
            QPushButton:pressed {{
                background-color: {"#DC2626" if self.is_close else "rgba(255, 255, 255, 0.2)"};
            }}
        """)


class TitleBar(QWidget):
    """Custom title bar featuring LensFlow logo badge, title, and Minimize/Maximize/Close buttons."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedHeight(44)
        self.setObjectName("TitleBar")
        self.setStyleSheet("""
            QWidget#TitleBar {
                background-color: #0B0B0F;
                border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 0, 0)
        layout.setSpacing(0)

        # ── LF Monogram Logo Badge ───────────────────────────────────────
        self.logo_badge = _LFBadge()
        layout.addWidget(self.logo_badge, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addSpacing(10)

        # ── Title Brand Label ───────────────────────────────────────────
        brand = QLabel("LensFlow")
        brand.setStyleSheet(
            "color: #FFFFFF; font-size: 14px; font-weight: 600; letter-spacing: -0.2px;"
        )
        layout.addWidget(brand, 0, Qt.AlignmentFlag.AlignVCenter)

        layout.addStretch()

        # ── Window Control Buttons ──────────────────────────────────────
        self.btn_minimize = WindowControlButton("\u2014", tooltip="Minimize")
        self.btn_maximize = WindowControlButton("\u25A1", tooltip="Maximize")
        self.btn_close = WindowControlButton("\u2715", tooltip="Close", is_close=True)

        layout.addWidget(self.btn_minimize)
        layout.addWidget(self.btn_maximize)
        layout.addWidget(self.btn_close)

        # Connect actions
        self.btn_minimize.clicked.connect(self._minimize)
        self.btn_maximize.clicked.connect(self._toggle_maximize)
        self.btn_close.clicked.connect(self._close)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            w = self.window()
            if w and w.windowHandle():
                w.windowHandle().startSystemMove()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_maximize()
        super().mouseDoubleClickEvent(event)

    def _minimize(self):
        w = self.window()
        if w:
            w.showMinimized()

    def _toggle_maximize(self):
        w = self.window()
        if w:
            if w.isMaximized():
                w.showNormal()
                self.btn_maximize.set_symbol("\u25A1")
                self.btn_maximize.setToolTip("Maximize")
            else:
                w.showMaximized()
                self.btn_maximize.set_symbol("\u2749")  # Restore icon symbol
                self.btn_maximize.setToolTip("Restore")

    def _close(self):
        w = self.window()
        if w:
            w.close()


class _LFBadge(QWidget):
    """Small 28x28 rounded badge with 'LF' monogram."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(28, 28)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = float(self.width()), float(self.height())

        grad = QRadialGradient(w * 0.4, h * 0.35, w * 0.6)
        grad.setColorAt(0.0, QColor(96, 165, 250))
        grad.setColorAt(1.0, QColor(99, 102, 241))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawRoundedRect(0, 0, int(w), int(h), 7, 7)

        p.setPen(QColor("#FFFFFF"))
        font = QFont("Inter", 9)
        font.setWeight(QFont.Weight.Bold)
        p.setFont(font)
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "LF")

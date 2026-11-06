"""LensFlow - Custom Window Title Bar Controls

Frameless custom title bar providing LensFlow brand identity, window dragging,
and Windows 11 style Minimize, Maximize/Restore, and Close buttons.
"""

from typing import Optional
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPainter, QColor, QFont, QRadialGradient, QBrush
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton
)

from frontend.styles.theme import (
    PAGE_BG,
    ON_PRIMARY,
    OVERLAY_2,
    OVERLAY_BORDER,
    TEXT_STRONG,
    BG_DARK,
    BORDER,
    PRIMARY_TEXT,
    SECONDARY_TEXT,
    TEXT_MUTED,
    PRIMARY,
    SECONDARY_ACCENT,
    ERROR,
)
from backend.app_info import APP_NAME


class WindowControlButton(QPushButton):
    """Minimal window control button (Minimize, Maximize, Close)."""

    def __init__(self, symbol: str, tooltip: str = "", is_close: bool = False, parent=None):
        super().__init__(symbol, parent)
        self.setFixedSize(46, 38)
        self.setToolTip(tooltip)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.is_close = is_close
        self._apply_style()

    def set_symbol(self, symbol: str):
        self.setText(symbol)

    def _apply_style(self):
        hover_bg = ERROR if self.is_close else OVERLAY_2
        # White on the red close button; the theme's strongest text otherwise.
        hover_fg = "#FFFFFF" if self.is_close else TEXT_STRONG

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {SECONDARY_TEXT};
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
                background-color: {"#DC2626" if self.is_close else OVERLAY_BORDER};
            }}
        """)


class TitleBar(QWidget):
    """Custom title bar featuring LensFlow logo badge, title, and Minimize/Maximize/Close buttons."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedHeight(42)
        self.setObjectName("TitleBar")
        self.setStyleSheet(f"""
            QWidget#TitleBar {{
                background-color: {PAGE_BG};
                border-bottom: 1px solid {BORDER};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 8, 0)
        layout.setSpacing(0)

        # ── LF Monogram Logo Badge ───────────────────────────────────────
        self.logo_badge = _LFBadge()
        layout.addWidget(self.logo_badge, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addSpacing(10)

        # ── Title Brand Label ───────────────────────────────────────────
        brand = QLabel(APP_NAME)
        brand.setStyleSheet(f"""
            color: {PRIMARY_TEXT};
            font-size: 13px;
            font-weight: 600;
            letter-spacing: -0.2px;
        """)
        layout.addWidget(brand, 0, Qt.AlignmentFlag.AlignVCenter)

        layout.addStretch()

        # ── Window Control Buttons ──────────────────────────────────────
        self.btn_minimize = WindowControlButton("—", tooltip="Minimize")
        self.btn_maximize = WindowControlButton("□", tooltip="Maximize")
        self.btn_close = WindowControlButton("✕", tooltip="Close", is_close=True)

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
                self.btn_maximize.set_symbol("□")
                self.btn_maximize.setToolTip("Maximize")
            else:
                w.showMaximized()
                self.btn_maximize.set_symbol("❐")
                self.btn_maximize.setToolTip("Restore")

    def _close(self):
        w = self.window()
        if w:
            w.close()


class _LFBadge(QWidget):
    """Small 26x26 rounded badge with 'LF' monogram."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(26, 26)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = float(self.width()), float(self.height())

        grad = QRadialGradient(w * 0.4, h * 0.35, w * 0.6)
        grad.setColorAt(0.0, QColor(SECONDARY_ACCENT))
        grad.setColorAt(1.0, QColor(PRIMARY))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawRoundedRect(0, 0, int(w), int(h), 6, 6)

        p.setPen(QColor(ON_PRIMARY))
        font = QFont("Inter", 8)
        font.setWeight(QFont.Weight.Bold)
        p.setFont(font)
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "LF")

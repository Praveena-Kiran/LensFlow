"""LensFlow - Right Command Center Panel

Today's Focus card, System Status indicators, and Quick Launch list.
Supports smooth collapsing and expanding with width animations.
"""

from typing import Optional
from PySide6.QtCore import Qt, QRectF, QPropertyAnimation, QEasingCurve, Signal
from PySide6.QtGui import QPainter, QColor, QBrush, QFont, QPen
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QSizePolicy
)

from frontend.styles.theme import (
    BG_DARK,
    SURFACE,
    SURFACE_HOVER,
    BORDER,
    PRIMARY_TEXT,
    SECONDARY_TEXT,
    TEXT_MUTED,
    PRIMARY,
    PRIMARY_HOVER,
    SUCCESS,
    WARNING,
    INFO,
)


# ────────────────────────────────────────────────────────────────────────────
#  Mini Progress Bar
# ────────────────────────────────────────────────────────────────────────────

class _ProgressBar(QWidget):
    """Thin rounded progress bar with primary brand fill."""

    def __init__(self, value: float = 0.65, color: str = PRIMARY, parent=None):
        super().__init__(parent)
        self.setFixedHeight(5)
        self._value = max(0.0, min(1.0, value))
        self._color = QColor(color)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = float(self.width()), float(self.height())
        r = h / 2.0

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(255, 255, 255, 14)))
        p.drawRoundedRect(QRectF(0, 0, w, h), r, r)

        fw = w * self._value
        if fw > 0:
            p.setBrush(QBrush(self._color))
            p.drawRoundedRect(QRectF(0, 0, fw, h), r, r)


# ────────────────────────────────────────────────────────────────────────────
#  Status Row
# ────────────────────────────────────────────────────────────────────────────

class _StatusRow(QWidget):
    """Single status item: semantic glowing dot + label + value."""

    def __init__(self, dot_color: str, label: str, value: str, value_color: str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(10)

        # Indicator Dot
        dot = QWidget()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(f"""
            background-color: {dot_color};
            border-radius: 4px;
        """)
        layout.addWidget(dot, 0, Qt.AlignmentFlag.AlignVCenter)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {SECONDARY_TEXT}; font-size: 12px; font-weight: 400;")
        layout.addWidget(lbl, 1)

        val = QLabel(value)
        val.setStyleSheet(f"""
            color: {value_color};
            font-size: 11px;
            font-weight: 600;
        """)
        layout.addWidget(val, 0, Qt.AlignmentFlag.AlignRight)


# ────────────────────────────────────────────────────────────────────────────
#  Quick-Launch Row
# ────────────────────────────────────────────────────────────────────────────

class _QuickLaunchRow(QPushButton):
    """Quick launch item with muted dot + label + chevron."""

    def __init__(self, dot_color: str, label: str, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(34)
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 8px;
                padding: 0px 8px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.05);
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(10)

        dot = QWidget()
        dot.setFixedSize(6, 6)
        dot.setStyleSheet(f"background-color: {dot_color}; border-radius: 3px;")
        layout.addWidget(dot, 0, Qt.AlignmentFlag.AlignVCenter)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {PRIMARY_TEXT}; font-size: 12px; font-weight: 400;")
        layout.addWidget(lbl, 1)

        chevron = QLabel("›")
        chevron.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 16px; font-weight: 400;")
        layout.addWidget(chevron, 0, Qt.AlignmentFlag.AlignRight)


# ────────────────────────────────────────────────────────────────────────────
#  Section Header
# ────────────────────────────────────────────────────────────────────────────

def _section_header(text: str, icon_char: str = "") -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(8)
    if icon_char:
        ic = QLabel(icon_char)
        ic.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px;")
        row.addWidget(ic, 0, Qt.AlignmentFlag.AlignVCenter)
    lbl = QLabel(text)
    lbl.setStyleSheet(f"""
        color: {PRIMARY_TEXT};
        font-size: 13px;
        font-weight: 600;
        letter-spacing: -0.1px;
    """)
    row.addWidget(lbl, 1)
    return row


# ────────────────────────────────────────────────────────────────────────────
#  Right Panel Widget (Collapsible)
# ────────────────────────────────────────────────────────────────────────────

class RightPanel(QFrame):
    """Right command center sidebar with collapsible animation."""

    toggled = Signal(bool)  # Emits current collapsed state (True = collapsed)

    EXPANDED_WIDTH = 300
    COLLAPSED_WIDTH = 44

    def __init__(self, is_collapsed: bool = False, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.is_collapsed = is_collapsed
        self.setObjectName("RightPanel")

        initial_width = self.COLLAPSED_WIDTH if is_collapsed else self.EXPANDED_WIDTH
        self.setFixedWidth(initial_width)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._apply_style()

        # Root Layout
        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(8, 16, 8, 16)
        self._root_layout.setSpacing(0)

        # ── Toggle Header Button ────────────────────────────────────────
        self.toggle_btn = QPushButton()
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setFixedSize(28, 28)
        self.toggle_btn.setToolTip("Toggle Command Center Panel")
        self.toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.04);
                border: 1px solid {BORDER};
                border-radius: 8px;
                color: {SECONDARY_TEXT};
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba(124, 92, 255, 0.15);
                border: 1px solid rgba(124, 92, 255, 0.40);
                color: #FFFFFF;
            }}
        """)
        self.toggle_btn.clicked.connect(self.toggle_collapse)

        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(4, 0, 4, 14)
        top_bar.addWidget(self.toggle_btn, 0, Qt.AlignmentFlag.AlignLeft)
        self._root_layout.addLayout(top_bar)

        # ── Content Area Container Widget ───────────────────────────────
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(8, 0, 8, 0)
        content_layout.setSpacing(0)

        # ── Today's Focus ───────────────────────────────────────────────
        content_layout.addLayout(_section_header("Today's Focus"))
        content_layout.addSpacing(10)

        focus_card = QFrame()
        focus_card.setObjectName("FocusCard")
        focus_card.setStyleSheet(f"""
            QFrame#FocusCard {{
                background-color: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)
        fc_layout = QVBoxLayout(focus_card)
        fc_layout.setContentsMargins(14, 12, 14, 12)
        fc_layout.setSpacing(8)

        cont = QLabel("Continue where you left off")
        cont.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-weight: 400;")
        fc_layout.addWidget(cont)

        row = QHBoxLayout()
        task = QLabel("LensFlow UI Polish")
        task.setStyleSheet(f"color: {PRIMARY_TEXT}; font-size: 13px; font-weight: 600;")
        row.addWidget(task, 1)
        pct = QLabel("75%")
        pct.setStyleSheet(f"color: {SECONDARY_TEXT}; font-size: 11px; font-weight: 500;")
        row.addWidget(pct, 0)
        fc_layout.addLayout(row)

        fc_layout.addWidget(_ProgressBar(0.75, PRIMARY))
        fc_layout.addSpacing(4)

        resume = QPushButton("Resume  →")
        resume.setCursor(Qt.CursorShape.PointingHandCursor)
        resume.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {PRIMARY};
                border: none;
                font-size: 11px;
                font-weight: 600;
                text-align: right;
                padding: 0px;
            }}
            QPushButton:hover {{ color: {PRIMARY_HOVER}; }}
        """)
        resume.setFixedHeight(20)
        fc_layout.addWidget(resume, 0, Qt.AlignmentFlag.AlignRight)

        content_layout.addWidget(focus_card)
        content_layout.addSpacing(22)

        # ── System Status (Semantic Meaningful Colors) ───────────────────
        content_layout.addLayout(_section_header("System Status"))
        content_layout.addSpacing(8)

        statuses = [
            (SUCCESS, "Camera", "Connected", SUCCESS),
            (WARNING, "Gesture Engine", "Idle", WARNING),
            (INFO, "Microphone", "Ready", INFO),
            (PRIMARY, "AI Assistant", "Online", PRIMARY),
        ]
        for dot, label, val, vc in statuses:
            content_layout.addWidget(_StatusRow(dot, label, val, vc))

        content_layout.addSpacing(22)

        # ── Quick Launch (Muted subtle indicator dots) ───────────────────
        content_layout.addLayout(_section_header("Quick Launch"))
        content_layout.addSpacing(8)

        apps = [
            ("#5B8CFF", "VS Code"),
            ("#F59E0B", "Chrome"),
            ("#8B93A7", "GitHub"),
            ("#22C55E", "Terminal"),
            ("#7C5CFF", "Notion"),
        ]
        for dot, label in apps:
            content_layout.addWidget(_QuickLaunchRow(dot, label))

        content_layout.addStretch()

        self._root_layout.addWidget(self.content_widget, 1)

        # ── Width Animation Setup ───────────────────────────────────────
        self._anim = QPropertyAnimation(self, b"size", self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._update_toggle_icon()
        self.content_widget.setVisible(not self.is_collapsed)

    def toggle_collapse(self):
        self.set_collapsed(not self.is_collapsed)

    def set_collapsed(self, collapsed: bool):
        self.is_collapsed = collapsed
        target_width = self.COLLAPSED_WIDTH if collapsed else self.EXPANDED_WIDTH

        if not collapsed:
            self.content_widget.setVisible(True)

        self.setMinimumWidth(self.COLLAPSED_WIDTH)
        self._anim.stop()
        self._anim.setStartValue(self.width())
        self._anim.setEndValue(target_width)

        def _on_finish():
            self.setFixedWidth(target_width)
            if collapsed:
                self.content_widget.setVisible(False)
            self._update_toggle_icon()
            self.toggled.emit(collapsed)
            try:
                self._anim.finished.disconnect(_on_finish)
            except RuntimeError:
                pass

        self._anim.finished.connect(_on_finish)
        self._anim.start()

    def _update_toggle_icon(self):
        self.toggle_btn.setText("«" if self.is_collapsed else "»")

    def _apply_style(self):
        self.setStyleSheet(f"""
            QFrame#RightPanel {{
                background-color: {BG_DARK};
                border-left: 1px solid {BORDER};
            }}
        """)

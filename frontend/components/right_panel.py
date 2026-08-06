"""LensFlow - Right Panel

Today's Focus card, System Status indicators, and Quick Launch list.
Supports smooth collapsing and expanding with width animations.
"""

from typing import Optional
from PySide6.QtCore import Qt, QRectF, QPropertyAnimation, QEasingCurve, Signal
from PySide6.QtGui import QPainter, QColor, QBrush, QFont
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QSizePolicy
)


# ────────────────────────────────────────────────────────────────────────────
#  Mini Progress Bar
# ────────────────────────────────────────────────────────────────────────────

class _ProgressBar(QWidget):
    """Thin rounded progress bar."""

    def __init__(self, value: float = 0.5, color: str = "#3B82F6", parent=None):
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
        p.setBrush(QBrush(QColor(255, 255, 255, 12)))
        p.drawRoundedRect(QRectF(0, 0, w, h), r, r)

        fw = w * self._value
        if fw > 0:
            p.setBrush(QBrush(self._color))
            p.drawRoundedRect(QRectF(0, 0, fw, h), r, r)


# ────────────────────────────────────────────────────────────────────────────
#  Status Row
# ────────────────────────────────────────────────────────────────────────────

class _StatusRow(QWidget):
    """Single status item: coloured dot + label + value."""

    def __init__(self, dot_color: str, label: str, value: str, value_color: str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        dot = QWidget()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(f"background-color: {dot_color}; border-radius: 4px;")
        layout.addWidget(dot, 0, Qt.AlignmentFlag.AlignVCenter)

        lbl = QLabel(label)
        lbl.setStyleSheet("color: #D1D5DB; font-size: 13px; font-weight: 400;")
        layout.addWidget(lbl, 1)

        val = QLabel(value)
        val.setStyleSheet(f"color: {value_color}; font-size: 12px; font-weight: 600;")
        layout.addWidget(val, 0, Qt.AlignmentFlag.AlignRight)


# ────────────────────────────────────────────────────────────────────────────
#  Quick-Launch Row
# ────────────────────────────────────────────────────────────────────────────

class _QuickLaunchRow(QPushButton):
    """Quick launch item with dot + label + chevron."""

    def __init__(self, dot_color: str, label: str, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(34)
        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.04);
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 4, 0)
        layout.setSpacing(10)

        dot = QWidget()
        dot.setFixedSize(7, 7)
        dot.setStyleSheet(f"background-color: {dot_color}; border-radius: 3px;")
        layout.addWidget(dot, 0, Qt.AlignmentFlag.AlignVCenter)

        lbl = QLabel(label)
        lbl.setStyleSheet("color: #D1D5DB; font-size: 13px; font-weight: 400;")
        layout.addWidget(lbl, 1)

        chevron = QLabel("\u203A")
        chevron.setStyleSheet("color: #6B7280; font-size: 16px;")
        layout.addWidget(chevron, 0, Qt.AlignmentFlag.AlignRight)


# ────────────────────────────────────────────────────────────────────────────
#  Section Header
# ────────────────────────────────────────────────────────────────────────────

def _section_header(text: str, icon_char: str = "") -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(8)
    if icon_char:
        ic = QLabel(icon_char)
        ic.setStyleSheet("color: #9CA3AF; font-size: 14px;")
        row.addWidget(ic, 0, Qt.AlignmentFlag.AlignVCenter)
    lbl = QLabel(text)
    lbl.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: 600; letter-spacing: -0.1px;")
    row.addWidget(lbl, 1)
    return row


# ────────────────────────────────────────────────────────────────────────────
#  Right Panel Widget (Collapsible)
# ────────────────────────────────────────────────────────────────────────────

class RightPanel(QFrame):
    """Right sidebar: Today's Focus, System Status, Quick Launch.

    Supports smooth collapsible/expandable width animation.
    """

    toggled = Signal(bool)  # Emits current collapsed state (True = collapsed)

    EXPANDED_WIDTH = 320
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
        self.toggle_btn.setToolTip("Toggle Panel (Collapse/Expand)")
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                color: #9CA3AF;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(59, 130, 246, 0.15);
                border: 1px solid rgba(59, 130, 246, 0.4);
                color: #FFFFFF;
            }
        """)
        self.toggle_btn.clicked.connect(self.toggle_collapse)

        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(4, 0, 4, 12)
        top_bar.addWidget(self.toggle_btn, 0, Qt.AlignmentFlag.AlignLeft)
        self._root_layout.addLayout(top_bar)

        # ── Content Area Container Widget ───────────────────────────────
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(12, 0, 12, 0)
        content_layout.setSpacing(0)

        # ── Today's Focus ───────────────────────────────────────────────
        content_layout.addLayout(_section_header("Today's Focus"))
        content_layout.addSpacing(14)

        focus_card = QFrame()
        focus_card.setObjectName("FocusCard")
        focus_card.setStyleSheet("""
            QFrame#FocusCard {
                background-color: #16161E;
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 14px;
            }
        """)
        fc_layout = QVBoxLayout(focus_card)
        fc_layout.setContentsMargins(14, 12, 14, 12)
        fc_layout.setSpacing(8)

        cont = QLabel("Continue where you left off")
        cont.setStyleSheet("color: #6B7280; font-size: 11px; font-weight: 400;")
        fc_layout.addWidget(cont)

        row = QHBoxLayout()
        task = QLabel("LensFlow UI Redesign")
        task.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 600;")
        row.addWidget(task, 1)
        pct = QLabel("65%")
        pct.setStyleSheet("color: #9CA3AF; font-size: 12px; font-weight: 500;")
        row.addWidget(pct, 0)
        fc_layout.addLayout(row)

        fc_layout.addWidget(_ProgressBar(0.65, "#3B82F6"))
        fc_layout.addSpacing(4)

        resume = QPushButton("Resume  \u2192")
        resume.setCursor(Qt.CursorShape.PointingHandCursor)
        resume.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #9CA3AF;
                border: none;
                font-size: 12px;
                font-weight: 500;
                text-align: right;
                padding: 0px;
            }
            QPushButton:hover { color: #FFFFFF; }
        """)
        resume.setFixedHeight(20)
        fc_layout.addWidget(resume, 0, Qt.AlignmentFlag.AlignRight)

        content_layout.addWidget(focus_card)
        content_layout.addSpacing(24)

        # ── System Status ───────────────────────────────────────────────
        content_layout.addLayout(_section_header("System Status"))
        content_layout.addSpacing(12)

        statuses = [
            ("#22C55E", "Camera", "Connected", "#22C55E"),
            ("#F59E0B", "Gesture Engine", "Idle", "#F59E0B"),
            ("#3B82F6", "Microphone", "Ready", "#3B82F6"),
            ("#8B5CF6", "AI Assistant", "Online", "#8B5CF6"),
        ]
        for dot, label, val, vc in statuses:
            content_layout.addWidget(_StatusRow(dot, label, val, vc))

        content_layout.addSpacing(24)

        # ── Quick Launch ────────────────────────────────────────────────
        content_layout.addLayout(_section_header("Quick Launch"))
        content_layout.addSpacing(10)

        apps = [
            ("#3B82F6", "VS Code"),
            ("#F59E0B", "Chrome"),
            ("#9CA3AF", "GitHub"),
            ("#22C55E", "Terminal"),
            ("#8B5CF6", "Notion"),
        ]
        for dot, label in apps:
            content_layout.addWidget(_QuickLaunchRow(dot, label))

        content_layout.addStretch()

        self._root_layout.addWidget(self.content_widget, 1)

        # ── Width Animation Setup ───────────────────────────────────────
        self._anim = QPropertyAnimation(self, b"size", self)
        self._anim.setDuration(250)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._update_toggle_icon()
        self.content_widget.setVisible(not self.is_collapsed)

    def toggle_collapse(self):
        """Toggles right panel between expanded (270px) and collapsed (44px)."""
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
        # When collapsed, show chevron right / expand symbol '›' or '«'
        # When expanded, show chevron right '»' or '›'
        self.toggle_btn.setText("«" if self.is_collapsed else "»")

    def _apply_style(self):
        self.setStyleSheet("""
            QFrame#RightPanel {
                background-color: #0E0E14;
                border-left: 1px solid rgba(255, 255, 255, 0.06);
            }
        """)

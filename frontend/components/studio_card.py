"""
LensFlow - Reusable Studio Card

Displays a studio card with a cohesive LensFlow brand dark aesthetic:
- Neutral dark card surface (#101118) and subtle border (#252936)
- Subtle brand gradient variation for studio icons
- Unified LensFlow Primary Indigo/Violet (#7C5CFF) Launch button
- Refined typography and capability tags
"""

from typing import Optional

from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import (
    QPainter,
    QColor,
    QFont,
    QRadialGradient,
    QBrush,
    QPen,
)
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
    QSizePolicy,
    QGraphicsDropShadowEffect,
    QMenu,
)

from frontend.styles.theme import (
    SURFACE,
    SURFACE_HOVER,
    BORDER,
    BORDER_HOVER,
    PRIMARY,
    PRIMARY_HOVER,
    PRIMARY_PRESSED,
    PRIMARY_TEXT,
    SECONDARY_TEXT,
    TEXT_MUTED,
    MENU_STYLE,
)


class _IconBadge(QWidget):
    """Refined circular icon badge with subtle brand tint."""

    def __init__(
        self,
        symbol: str,
        color: str = PRIMARY,
        size: int = 38,
        parent=None
    ):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._symbol = symbol
        self._color = QColor(color)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = float(min(self.width(), self.height()))

        # Background with subtle brand tint
        bg_color = QColor(self._color)
        bg_color.setAlpha(30)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(bg_color))
        p.drawEllipse(QRectF(0, 0, s, s))

        # Delicate border ring
        border_color = QColor(self._color)
        border_color.setAlpha(80)
        p.setPen(QPen(border_color, 1.2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(0.6, 0.6, s - 1.2, s - 1.2))

        # Soft top radial highlight for glass feel
        grad = QRadialGradient(s * 0.5, s * 0.25, s * 0.6)
        grad.setColorAt(0.0, QColor(255, 255, 255, 30))
        grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawEllipse(QRectF(1, 1, s - 2, s - 2))

        # Centered Icon / Text Symbol
        symbol_color = QColor(self._color).lighter(135)
        p.setPen(symbol_color)
        font = QFont("Inter", int(s * 0.32))
        font.setWeight(QFont.Weight.Bold)
        p.setFont(font)
        p.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            self._symbol
        )


class StudioCard(QFrame):
    """Unified LensFlow brand studio card widget."""

    # =========================================================
    # SIGNALS
    # =========================================================
    launch_clicked = Signal(str)
    studio_clicked = Signal(str)
    launch_all_requested = Signal(str)
    launch_event_requested = Signal(str, dict)

    # =========================================================
    # INIT
    # =========================================================
    def __init__(
        self,
        title: str,
        time_ago: str,
        description: str,
        apps: list,
        last_used: str,
        icon_symbol: str = "✦",
        accent: str = PRIMARY,
        studio_type: str = "built_in",
        events: Optional[list] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)

        self._title = title
        self._accent = accent
        self.studio_type = studio_type
        self.events = events or []

        self.setObjectName("StudioCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedSize(300, 225)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Drop Shadow
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(20)
        self._shadow.setOffset(0, 4)
        self._shadow.setColor(QColor(0, 0, 0, 70))
        self.setGraphicsEffect(self._shadow)

        self._apply_style()

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        # =====================================================
        # ROW 1: ICON + TITLE + TIME
        # =====================================================
        top = QHBoxLayout()
        top.setSpacing(12)

        badge = _IconBadge(icon_symbol, accent, size=38)
        top.addWidget(badge, 0, Qt.AlignmentFlag.AlignTop)

        title_col = QVBoxLayout()
        title_col.setSpacing(3)

        t = QLabel(title)
        t.setStyleSheet(f"""
            color: {PRIMARY_TEXT};
            font-size: 15px;
            font-weight: 600;
            letter-spacing: -0.2px;
        """)
        title_col.addWidget(t)

        desc = QLabel(description)
        desc.setWordWrap(True)
        desc.setMaximumHeight(34)
        desc.setStyleSheet(f"""
            color: {SECONDARY_TEXT};
            font-size: 12px;
            font-weight: 400;
            line-height: 1.3;
        """)
        title_col.addWidget(desc)

        top.addLayout(title_col, 1)

        time_lbl = QLabel(time_ago)
        time_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        time_lbl.setStyleSheet(f"""
            color: {TEXT_MUTED};
            font-size: 11px;
            font-weight: 500;
        """)
        top.addWidget(time_lbl, 0, Qt.AlignmentFlag.AlignTop)

        layout.addLayout(top)

        # =====================================================
        # ROW 2: APP CHIPS / TAGS
        # =====================================================
        chips_row = QHBoxLayout()
        chips_row.setSpacing(6)
        chips_row.setContentsMargins(0, 4, 0, 0)

        display_apps = apps[:3]
        if display_apps:
            for name in display_apps:
                chip = QLabel(name)
                chip.setStyleSheet(f"""
                    color: {SECONDARY_TEXT};
                    background-color: rgba(255, 255, 255, 0.04);
                    border: 1px solid {BORDER};
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: 500;
                    padding: 2px 8px;
                """)
                chip.setFixedHeight(22)
                chips_row.addWidget(chip)
        elif self.studio_type == "custom":
            event_count = len(self.events)
            count_label = f"{event_count} action{'s' if event_count != 1 else ''}"
            chip = QLabel(count_label)
            chip.setStyleSheet(f"""
                color: #A78BFA;
                background-color: rgba(124, 92, 255, 0.10);
                border: 1px solid rgba(124, 92, 255, 0.22);
                border-radius: 6px;
                font-size: 11px;
                font-weight: 500;
                padding: 2px 8px;
            """)
            chip.setFixedHeight(22)
            chips_row.addWidget(chip)

        chips_row.addStretch()
        layout.addLayout(chips_row)

        layout.addStretch()

        # =====================================================
        # ROW 3: LAST USED + UNIFIED LAUNCH BUTTON
        # =====================================================
        bottom = QHBoxLayout()
        bottom.setContentsMargins(0, 0, 0, 0)

        used_col = QVBoxLayout()
        used_col.setSpacing(1)

        used_label = QLabel("LAST USED")
        used_label.setStyleSheet(f"""
            color: {TEXT_MUTED};
            font-size: 9px;
            font-weight: 600;
            letter-spacing: 0.5px;
        """)
        used_col.addWidget(used_label)

        used_val = QLabel(last_used)
        used_val.setStyleSheet(f"""
            color: {SECONDARY_TEXT};
            font-size: 11px;
            font-weight: 500;
        """)
        used_col.addWidget(used_val)

        bottom.addLayout(used_col)
        bottom.addStretch()

        # Unified Primary Launch Button
        btn_label = "Launch  ▾" if self.studio_type == "custom" else "Launch  →"
        self.launch = QPushButton(btn_label)
        self.launch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.launch.setFixedSize(96, 32)

        self.launch.setStyleSheet(f"""
            QPushButton {{
                background-color: {PRIMARY};
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
                letter-spacing: 0.1px;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {PRIMARY_PRESSED};
            }}
        """)

        self.launch.clicked.connect(self._handle_launch_clicked)
        bottom.addWidget(self.launch, 0, Qt.AlignmentFlag.AlignBottom)

        layout.addLayout(bottom)

    # =========================================================
    # LAUNCH HANDLER
    # =========================================================
    def _handle_launch_clicked(self):
        if self.studio_type != "custom":
            self.launch_clicked.emit(self._title)
            return

        menu = self._create_custom_menu()
        menu.exec(self.launch.mapToGlobal(self.launch.rect().bottomLeft()))

    # =========================================================
    # CREATE CUSTOM STUDIO MENU
    # =========================================================
    def _create_custom_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(MENU_STYLE)

        launch_all = menu.addAction("▶  Launch All Events")
        launch_all.triggered.connect(
            lambda: self.launch_all_requested.emit(self._title)
        )

        if self.events:
            menu.addSeparator()
            for event in self.events:
                if not isinstance(event, dict):
                    continue

                event_name = event.get("name", "Unnamed Event")
                gesture = event.get("gesture", "")
                label = f"🎯  {event_name} ({gesture})" if gesture else f"⚡  {event_name}"

                action = menu.addAction(label)
                action.triggered.connect(
                    lambda checked=False, selected_event=event:
                        self.launch_event_requested.emit(self._title, selected_event)
                )

        return menu

    # =========================================================
    # STYLE & HOVER
    # =========================================================
    def _apply_style(self):
        self.setStyleSheet(f"""
            QFrame#StudioCard {{
                background-color: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 16px;
            }}
            QFrame#StudioCard:hover {{
                background-color: {SURFACE_HOVER};
                border: 1px solid {BORDER_HOVER};
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.launch.geometry().contains(event.position().toPoint()):
                super().mousePressEvent(event)
                return

            self.studio_clicked.emit(self._title)

        super().mousePressEvent(event)

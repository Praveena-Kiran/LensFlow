"""LensFlow - Hero Action Section

Features:
- Time-aware dynamic greeting ("Good Morning", "Good Afternoon", "Good Evening")
- Auto-updating clock timer for live greeting transitions
- Centred interactive glowing orb (breathing idle pulse, hover scale, gesture ripple)
- Connected 'Start Listening' CTA button with brand Indigo/Violet styling
"""

import datetime
from typing import Optional
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QFrame
)
from frontend.components.glow_orb import GlowOrb
from frontend.styles.theme import (
    PRIMARY_TEXT,
    SECONDARY_TEXT,
    TEXT_MUTED,
    PRIMARY,
    PRIMARY_HOVER,
    PRIMARY_PRESSED,
    SUCCESS,
)


def _greeting() -> str:
    """Returns time-aware greeting prefix based on current local system time."""
    h = datetime.datetime.now().hour
    if h < 12:
        return "Good Morning,"
    elif h < 17:
        return "Good Afternoon,"
    return "Good Evening,"


class HeroSection(QWidget):
    """Compact hero action section with dynamic greeting, interactive orb, and listening controls."""

    def __init__(self, user_name: str = "Praveena", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.user_name = user_name
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 12)
        layout.setSpacing(10)

        # ── Top Row: Dynamic Greeting + System Badge ─────────────────────
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)

        greeting_col = QVBoxLayout()
        greeting_col.setSpacing(4)

        # Title Row: "Good Evening, Praveena."
        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        self.greeting_prefix = QLabel(_greeting())
        self.greeting_prefix.setStyleSheet(f"""
            color: {PRIMARY_TEXT};
            font-size: 28px;
            font-weight: 700;
            letter-spacing: -0.5px;
        """)
        title_row.addWidget(self.greeting_prefix)

        self.greeting_name = QLabel(f"{user_name}.")
        self.greeting_name.setStyleSheet(f"""
            color: {PRIMARY};
            font-size: 28px;
            font-weight: 700;
            letter-spacing: -0.5px;
        """)
        title_row.addWidget(self.greeting_name)
        title_row.addStretch()
        greeting_col.addLayout(title_row)

        # Subtitle
        sub = QLabel("LensFlow AI Workspace · Ready to listen")
        sub.setStyleSheet(f"color: {SECONDARY_TEXT}; font-size: 13px; font-weight: 400;")
        greeting_col.addWidget(sub)

        top.addLayout(greeting_col, 1)

        # System Status Badge (Semantic Green)
        self.badge = QLabel("● SYSTEM READY")
        self.badge.setFixedHeight(26)
        self.badge.setStyleSheet(f"""
            color: {SUCCESS};
            background-color: rgba(34, 197, 94, 0.10);
            border: 1px solid rgba(34, 197, 94, 0.25);
            border-radius: 13px;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.6px;
            padding: 0px 12px;
        """)
        top.addWidget(self.badge, 0, Qt.AlignmentFlag.AlignTop)

        layout.addLayout(top)
        layout.addSpacing(2)

        # ── Interactive Glowing Orb (Compact Hero Center) ───────────────
        self.orb = GlowOrb(diameter=96)
        self.orb.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed
        )
        self.orb.setToolTip("Click to trigger gesture ripple / Hover to expand")
        layout.addWidget(self.orb, 0, Qt.AlignmentFlag.AlignHCenter)

        layout.addSpacing(2)

        # ── Start Listening CTA Button (Primary Brand Action) ───────────
        self.btn_listen = QPushButton("♪   Start Listening")
        self.btn_listen.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_listen.setFixedSize(170, 36)
        self.btn_listen.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(124, 92, 255, 0.35), stop:1 rgba(91, 140, 255, 0.35));
                color: #FFFFFF;
                border: 1px solid rgba(124, 92, 255, 0.45);
                border-radius: 18px;
                font-size: 12px;
                font-weight: 600;
                letter-spacing: 0.2px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(124, 92, 255, 0.55), stop:1 rgba(91, 140, 255, 0.55));
                border: 1px solid rgba(139, 112, 255, 0.75);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(104, 69, 236, 0.65), stop:1 rgba(91, 140, 255, 0.65));
            }}
        """)
        self.btn_listen.clicked.connect(self._on_listen_clicked)
        layout.addWidget(self.btn_listen, 0, Qt.AlignmentFlag.AlignHCenter)

        # ── Auto-updating greeting timer (checks every 60s) ─────────────
        self._clock_timer = QTimer(self)
        self._clock_timer.setInterval(60000)
        self._clock_timer.timeout.connect(self._update_greeting)
        self._clock_timer.start()

    def _update_greeting(self):
        """Updates greeting prefix if time period shifts."""
        self.greeting_prefix.setText(_greeting())

    def _on_listen_clicked(self):
        """Toggles listening mode on orb & updates button visual state."""
        new_mode = self.orb.toggle_listening()
        if new_mode == GlowOrb.MODE_LISTENING:
            self.btn_listen.setText("◉   Listening...")
            self.btn_listen.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(124, 92, 255, 0.60), stop:1 rgba(139, 112, 255, 0.60));
                    color: #FFFFFF;
                    border: 1px solid rgba(139, 112, 255, 0.85);
                    border-radius: 18px;
                    font-size: 12px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(124, 92, 255, 0.75), stop:1 rgba(139, 112, 255, 0.75));
                    border: 1px solid rgba(139, 112, 255, 1.0);
                }}
            """)
            self.badge.setText("● LISTENING")
            self.badge.setStyleSheet(f"""
                color: {PRIMARY_HOVER};
                background-color: rgba(124, 92, 255, 0.12);
                border: 1px solid rgba(124, 92, 255, 0.35);
                border-radius: 13px;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 0.6px;
                padding: 0px 12px;
            """)
        else:
            self.btn_listen.setText("♪   Start Listening")
            self.btn_listen.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(124, 92, 255, 0.35), stop:1 rgba(91, 140, 255, 0.35));
                    color: #FFFFFF;
                    border: 1px solid rgba(124, 92, 255, 0.45);
                    border-radius: 18px;
                    font-size: 12px;
                    font-weight: 600;
                    letter-spacing: 0.2px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(124, 92, 255, 0.55), stop:1 rgba(91, 140, 255, 0.55));
                    border: 1px solid rgba(139, 112, 255, 0.75);
                }}
            """)
            self.badge.setText("● SYSTEM READY")
            self.badge.setStyleSheet(f"""
                color: {SUCCESS};
                background-color: rgba(34, 197, 94, 0.10);
                border: 1px solid rgba(34, 197, 94, 0.25);
                border-radius: 13px;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 0.6px;
                padding: 0px 12px;
            """)

"""LensFlow - Hero Section

Features:
- Time-aware dynamic greeting ("Good Morning", "Good Afternoon", "Good Evening")
- Auto-updating clock timer for live greeting transitions
- Centred interactive glowing orb (breathing idle pulse, hover scale, gesture ripple)
- Connected 'Start Listening' toggle button
"""

import datetime
from typing import Optional
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy
)
from frontend.components.glow_orb import GlowOrb


def _greeting() -> str:
    """Returns time-aware greeting prefix based on current local system time."""
    h = datetime.datetime.now().hour
    if h < 12:
        return "Good Morning,"
    elif h < 17:
        return "Good Afternoon,"
    return "Good Evening,"


class HeroSection(QWidget):
    """Hero greeting area with dynamic time greeting, interactive orb, and listening controls."""

    def __init__(self, user_name: str = "Praveena", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.user_name = user_name
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Top Row: Dynamic Greeting + System Badge ─────────────────────
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)

        greeting_col = QVBoxLayout()
        greeting_col.setSpacing(6)

        # Dynamic Title Row: "Good Evening, Praveena."
        title_row = QHBoxLayout()
        title_row.setSpacing(0)

        self.greeting_prefix = QLabel(_greeting())
        self.greeting_prefix.setStyleSheet(
            "color: #FFFFFF; font-size: 34px; font-weight: 700; letter-spacing: -0.7px;"
        )
        title_row.addWidget(self.greeting_prefix)
        title_row.addSpacing(10)

        self.greeting_name = QLabel(f"{user_name}.")
        self.greeting_name.setStyleSheet(
            "color: #60A5FA; font-size: 34px; font-weight: 700; letter-spacing: -0.7px;"
        )
        title_row.addWidget(self.greeting_name)
        title_row.addStretch()
        greeting_col.addLayout(title_row)

        # Subtitles
        sub = QLabel("What are we building today?")
        sub.setStyleSheet("color: #9CA3AF; font-size: 15px; font-weight: 400;")
        greeting_col.addWidget(sub)

        sub2 = QLabel("Your personalized AI workspace.")
        sub2.setStyleSheet("color: #6B7280; font-size: 13px; font-weight: 400;")
        greeting_col.addWidget(sub2)

        top.addLayout(greeting_col, 1)

        # System Ready Badge
        self.badge = QLabel("SYSTEM READY")
        self.badge.setFixedHeight(28)
        self.badge.setStyleSheet("""
            color: #22C55E;
            background-color: rgba(34, 197, 94, 0.10);
            border: 1px solid rgba(34, 197, 94, 0.25);
            border-radius: 14px;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.8px;
            padding: 0px 14px;
        """)
        top.addWidget(self.badge, 0, Qt.AlignmentFlag.AlignTop)

        layout.addLayout(top)
        layout.addSpacing(8)

        # ── Centred Interactive Glowing Orb ─────────────────────────────
        self.orb = GlowOrb(diameter=120)
        self.orb.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed
        )
        self.orb.setToolTip("Click to test gesture ripple effect / Hover to expand")
        layout.addWidget(self.orb, 0, Qt.AlignmentFlag.AlignHCenter)

        layout.addSpacing(2)

        # ── Start Listening Action Button ───────────────────────────────
        self.btn_listen = QPushButton("\u266A   Start Listening")
        self.btn_listen.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_listen.setFixedSize(180, 42)
        self.btn_listen.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(59, 130, 246, 0.25), stop:1 rgba(99, 102, 241, 0.25));
                color: #FFFFFF;
                border: 1px solid rgba(59, 130, 246, 0.35);
                border-radius: 21px;
                font-size: 13px;
                font-weight: 600;
                letter-spacing: 0.2px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(59, 130, 246, 0.45), stop:1 rgba(99, 102, 241, 0.45));
                border: 1px solid rgba(59, 130, 246, 0.65);
            }
        """)
        self.btn_listen.clicked.connect(self._on_listen_clicked)
        layout.addWidget(self.btn_listen, 0, Qt.AlignmentFlag.AlignHCenter)

        # ── Auto-updating greeting timer (checks every 60s) ─────────────
        self._clock_timer = QTimer(self)
        self._clock_timer.setInterval(60000)  # 60 seconds
        self._clock_timer.timeout.connect(self._update_greeting)
        self._clock_timer.start()

    def _update_greeting(self):
        """Updates greeting prefix if time period shifts."""
        self.greeting_prefix.setText(_greeting())

    def _on_listen_clicked(self):
        """Toggles listening mode on orb & updates button visual state."""
        new_mode = self.orb.toggle_listening()
        if new_mode == GlowOrb.MODE_LISTENING:
            self.btn_listen.setText("\u25C9   Listening...")
            self.btn_listen.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(168, 85, 247, 0.45), stop:1 rgba(59, 130, 246, 0.45));
                    color: #FFFFFF;
                    border: 1px solid rgba(168, 85, 247, 0.7);
                    border-radius: 21px;
                    font-size: 13px;
                    font-weight: 600;
                }
            """)
            self.badge.setText("LISTENING")
            self.badge.setStyleSheet("""
                color: #A855F7;
                background-color: rgba(168, 85, 247, 0.12);
                border: 1px solid rgba(168, 85, 247, 0.35);
                border-radius: 14px;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 0.8px;
                padding: 0px 14px;
            """)
        else:
            self.btn_listen.setText("\u266A   Start Listening")
            self.btn_listen.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(59, 130, 246, 0.25), stop:1 rgba(99, 102, 241, 0.25));
                    color: #FFFFFF;
                    border: 1px solid rgba(59, 130, 246, 0.35);
                    border-radius: 21px;
                    font-size: 13px;
                    font-weight: 600;
                }
            """)
            self.badge.setText("SYSTEM READY")
            self.badge.setStyleSheet("""
                color: #22C55E;
                background-color: rgba(34, 197, 94, 0.10);
                border: 1px solid rgba(34, 197, 94, 0.25);
                border-radius: 14px;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 0.8px;
                padding: 0px 14px;
            """)

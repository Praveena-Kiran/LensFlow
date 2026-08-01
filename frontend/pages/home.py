"""LensFlow - Home Page

Composes the Hero section, Studio cards row, and right panel
into a responsive scrollable Home screen.
"""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QSizePolicy, QPushButton
)
from frontend.components.hero_section import HeroSection
from frontend.components.studio_card import StudioCard
from frontend.components.right_panel import RightPanel


class HomePage(QWidget):
    """Home page assembling hero, studios grid, and the right focus panel."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("HomePage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("QWidget#HomePage { background-color: #0B0B0F; }")

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Scrollable centre content ───────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        scroll.setWidget(content)

        main = QVBoxLayout(content)
        main.setContentsMargins(40, 32, 40, 40)
        main.setSpacing(0)
        main.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Hero section
        self.hero = HeroSection()
        main.addWidget(self.hero)

        main.addSpacing(36)

        # Studios section header
        self._build_studios_header(main)

        main.addSpacing(16)

        # Studio cards row
        self._build_studios_row(main)

        main.addStretch()

        outer.addWidget(scroll, 1)

        # ── Right panel ─────────────────────────────────────────────────
        self.right_panel = RightPanel()
        outer.addWidget(self.right_panel)

    def _build_studios_header(self, parent: QVBoxLayout):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Your Studios")
        title.setStyleSheet(
            "color: #FFFFFF; font-size: 18px; font-weight: 600; letter-spacing: -0.2px;"
        )
        row.addWidget(title)
        row.addStretch()

        create = QPushButton("+ Create Studio")
        create.setCursor(Qt.CursorShape.PointingHandCursor)
        create.setFixedHeight(30)
        create.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #60A5FA;
                border: none;
                font-size: 13px;
                font-weight: 600;
                padding: 0px 8px;
            }
            QPushButton:hover { color: #93C5FD; }
        """)
        row.addWidget(create)
        parent.addLayout(row)

    def _build_studios_row(self, parent: QVBoxLayout):
        row = QHBoxLayout()
        row.setSpacing(16)

        studios = [
            {
                "title": "Coding Studio",
                "time_ago": "2 hours ago",
                "description": "VS Code, Terminal, GitHub and documentation ready to go.",
                "apps": ["VS Code", "Terminal", "GitHub", "Docs"],
                "last_used": "Today  \u2022  2:41 PM",
                "icon_symbol": "</>",
                "accent": "#3B82F6",
            },
            {
                "title": "Study Studio",
                "time_ago": "Yesterday",
                "description": "Notion, browser research, notes and flashcards.",
                "apps": ["Notion", "Browser", "Notes"],
                "last_used": "Yesterday  \u2022  6:30 PM",
                "icon_symbol": "St",
                "accent": "#8B5CF6",
            },
            {
                "title": "Design Studio",
                "time_ago": "3 days ago",
                "description": "Figma, color tools, assets and inspiration board.",
                "apps": ["Figma", "Colors", "Assets"],
                "last_used": "3 days ago  \u2022  11:20 AM",
                "icon_symbol": "Ds",
                "accent": "#EC4899",
            },
        ]

        for s in studios:
            card = StudioCard(**s)
            row.addWidget(card)

        parent.addLayout(row)

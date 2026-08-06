"""LensFlow - Home Page

Composes the Hero section, Studio cards row, and right panel
into a responsive scrollable Home screen.
"""


from frontend.pages.presentation_page import PresentationPage
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QFrame,
    QPushButton,
)

from frontend.components.hero_section import HeroSection
from frontend.components.studio_card import StudioCard
from frontend.components.right_panel import RightPanel
from frontend.layouts.flow_layout import FlowLayout

class HomePage(QWidget):
    """Home page assembling hero, studios grid, and the right focus panel."""

    studio_selected = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.setObjectName("HomePage")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(
            "QWidget#HomePage { background-color: #0B0B0F; }"
        )

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.content = QWidget()
        self.content.setStyleSheet("background: transparent;")
        self.scroll.setWidget(self.content)

        main = QVBoxLayout(self.content)
        main.setContentsMargins(40, 32, 40, 40)
        main.setSpacing(0)
        main.setAlignment(Qt.AlignTop)

        # Hero
        self.hero = HeroSection()
        hero_container = QWidget()
        hero_layout = QVBoxLayout(hero_container)
        hero_layout.setContentsMargins(0, 0, 0, 0)
        hero_layout.setSpacing(0)
        hero_layout.setAlignment(Qt.AlignTop)

        hero_layout.addWidget(self.hero, 0, Qt.AlignTop)

        main.addWidget(hero_container, 0, Qt.AlignTop)
        main.addSpacing(8)

        # Header
        self._build_studios_header(main)

        main.addSpacing(16)

        # Cards
        self._build_studios_row(main)

        main.addStretch()

        outer.addWidget(self.scroll, 1)

        # Right Panel
        self.right_panel = RightPanel()
        self.right_panel.setObjectName("RightPanel")
        self.right_panel.setMinimumWidth(280)
        self.right_panel.setMaximumWidth(320)

        outer.addWidget(self.right_panel)
        self._update_right_panel()
        self.presentation_page = PresentationPage()

       

    def _build_studios_header(self, parent):
        row = QHBoxLayout()

        title = QLabel("Your Studios")
        title.setStyleSheet("""
            color: white;
            font-size:18px;
            font-weight:600;
        """)

        row.addWidget(title)
        row.addStretch()

        create = QPushButton("+ Create Studio")
        create.setFixedHeight(30)
        create.setCursor(Qt.PointingHandCursor)
        create.setStyleSheet("""
            QPushButton{
                background:transparent;
                color:#60A5FA;
                border:none;
                font-size:13px;
                font-weight:600;
            }

            QPushButton:hover{
                color:#93C5FD;
            }
        """)

        row.addWidget(create)

        parent.addLayout(row)

    def _build_studios_row(self, parent):
        self.cards_container = QWidget()
        self.cards_container.setStyleSheet(
            "background: transparent;"
        )

        self.cards_layout = FlowLayout(
            spacing=16
        )

        studios = [
    {
        "title": "Presentation Studio",
        "time_ago": "Today",
        "description": "Control PowerPoint presentations using gestures and voice.",
        "apps": ["PowerPoint", "Camera", "Microphone"],
        "last_used": "Today • 2:41 PM",
        "icon_symbol": "Pr",
        "accent": "#3B82F6",
    },

    {
        "title": "Coding Studio",
        "time_ago": "Yesterday",
        "description": "Launch your development workspace and AI coding tools.",
        "apps": ["VS Code", "Terminal", "Git"],
        "last_used": "Yesterday • 6:30 PM",
        "icon_symbol": "</>",
        "accent": "#10B981",
    },

    {
        "title": "Gesture Studio",
        "time_ago": "3 days ago",
        "description": "Train, test and customize gesture recognition models.",
        "apps": ["MediaPipe", "Camera", "Models"],
        "last_used": "3 days ago • 11:20 AM",
        "icon_symbol": "✋",
        "accent": "#F59E0B",
    },

    {
        "title": "Automation Studio",
        "time_ago": "Never",
        "description": "Create automation flows triggered by gestures.",
        "apps": ["Flows", "Apps", "Actions"],
        "last_used": "Not yet",
        "icon_symbol": "⚡",
        "accent": "#8B5CF6",
    },
]


        for studio in studios:
            card = StudioCard(**studio)
            card.launch_clicked.connect(
                self.launch_studio
            )
            self.cards_layout.addWidget(card)


        self.cards_container.setLayout(
            self.cards_layout
        )

        parent.addWidget(
            self.cards_container
        )

    def launch_studio(self, studio_name):
        print(f"Launching {studio_name}")
        self.studio_selected.emit(studio_name)


    def _update_right_panel(self):
        if self.width() < 1100:
            self.right_panel.hide()
        else:
            self.right_panel.show()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_right_panel()

    
"""
LensFlow - Home Page

Dashboard containing:
- Hero section
- Studio cards
- Create Studio
- Persistent custom studios
"""

import json
import os
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

    studio_selected = Signal(str)
    create_studio_requested = Signal()

    def __init__(
        self,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)

        self.setObjectName("HomePage")

        self.setAttribute(
            Qt.WA_StyledBackground,
            True
        )

        self.setStyleSheet("""
            QWidget#HomePage {
                background-color: #0B0B0F;
            }
        """)

        # =====================================================
        # OUTER LAYOUT
        # =====================================================

        outer = QHBoxLayout(self)

        outer.setContentsMargins(
            0,
            0,
            0,
            0
        )

        outer.setSpacing(0)

        # =====================================================
        # SCROLL AREA
        # =====================================================

        self.scroll = QScrollArea()

        self.scroll.setWidgetResizable(True)

        self.scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.content = QWidget()

        self.content.setStyleSheet(
            "background: transparent;"
        )

        self.scroll.setWidget(
            self.content
        )

        main = QVBoxLayout(
            self.content
        )

        main.setContentsMargins(
            40,
            32,
            40,
            40
        )

        main.setSpacing(0)

        main.setAlignment(
            Qt.AlignmentFlag.AlignTop
        )

        # =====================================================
        # HERO
        # =====================================================

        self.hero = HeroSection()

        hero_container = QWidget()

        hero_layout = QVBoxLayout(
            hero_container
        )

        hero_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        hero_layout.setSpacing(0)

        hero_layout.addWidget(
            self.hero
        )

        main.addWidget(
            hero_container
        )

        main.addSpacing(8)

        # =====================================================
        # STUDIO HEADER
        # =====================================================

        self._build_studios_header(
            main
        )

        main.addSpacing(16)

        # =====================================================
        # STUDIO CARDS
        # =====================================================

        self._build_studios_row(
            main
        )

        main.addStretch()

        outer.addWidget(
            self.scroll,
            1
        )

        # =====================================================
        # RIGHT PANEL
        # =====================================================

        self.right_panel = RightPanel()

        self.right_panel.setObjectName(
            "RightPanel"
        )

        self.right_panel.setMinimumWidth(
            280
        )

        self.right_panel.setMaximumWidth(
            320
        )

        outer.addWidget(
            self.right_panel
        )

        self._update_right_panel()

    # =========================================================
    # HEADER
    # =========================================================

    def _build_studios_header(
        self,
        parent
    ):

        row = QHBoxLayout()

        title = QLabel(
            "Your Studios"
        )

        title.setStyleSheet("""
            color: white;
            font-size: 18px;
            font-weight: 600;
        """)

        row.addWidget(
            title
        )

        row.addStretch()

        create = QPushButton(
            "+ Create Studio"
        )

        create.setFixedHeight(
            30
        )

        create.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        create.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #60A5FA;
                border: none;
                font-size: 13px;
                font-weight: 600;
            }

            QPushButton:hover {
                color: #93C5FD;
            }
        """)

        create.clicked.connect(
            self.create_studio_requested.emit
        )

        row.addWidget(
            create
        )

        parent.addLayout(
            row
        )

    # =========================================================
    # STUDIO CARDS
    # =========================================================

    def _build_studios_row(
        self,
        parent
    ):

        self.cards_container = QWidget()

        self.cards_container.setStyleSheet(
            "background: transparent;"
        )

        self.cards_layout = FlowLayout(
            spacing=16
        )

        self.cards_container.setLayout(
            self.cards_layout
        )

        parent.addWidget(
            self.cards_container
        )

        self.refresh_studios()

    # =========================================================
    # LOAD STUDIOS
    # =========================================================

    def load_studios(self):

        config_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "backend",
                "config",
                "studios.json"
            )
        )

        try:

            with open(
                config_path,
                "r",
                encoding="utf-8"
            ) as f:

                studios = json.load(f)

            return studios

        except Exception as e:

            print(
                f"❌ Could not load studios.json: {e}"
            )

            return []

    # =========================================================
    # REFRESH DASHBOARD
    # =========================================================

    def refresh_studios(self):

        # Remove old cards

        while self.cards_layout.count():

            item = self.cards_layout.takeAt(0)

            widget = item.widget()

            if widget is not None:

                widget.deleteLater()

        # Load studios

        studios = self.load_studios()

        print(
            f"📂 Loaded {len(studios)} studios"
        )

        # Create cards

        for studio in studios:

            card = StudioCard(
                **{
                    key: value
                    for key, value in studio.items()
                    if key in {
                        "title",
                        "time_ago",
                        "description",
                        "apps",
                        "last_used",
                        "icon_symbol",
                        "accent"
                    }
                }
            )

            card.launch_clicked.connect(
                self.launch_studio
            )

            self.cards_layout.addWidget(
                card
            )

    # =========================================================
    # STUDIO CLICK
    # =========================================================

    def launch_studio(
        self,
        studio_name
    ):

        print(
            f"🎯 Studio selected: {studio_name}"
        )

        self.studio_selected.emit(
            studio_name
        )

    # =========================================================
    # RIGHT PANEL
    # =========================================================

    def _update_right_panel(self):

        if self.width() < 1100:

            self.right_panel.hide()

        else:

            self.right_panel.show()

    # =========================================================
    # RESIZE
    # =========================================================

    def resizeEvent(
        self,
        event
    ):

        super().resizeEvent(
            event
        )

        self._update_right_panel()
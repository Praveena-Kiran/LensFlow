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

    # =========================================================
    # SIGNALS
    # =========================================================

    # Built-in studio navigation
    studio_selected = Signal(str)

    # Create custom studio
    create_studio_requested = Signal()

    # Custom studio execution
    launch_all_events_requested = Signal(str)
    launch_specific_event_requested = Signal(str, dict)

    # =========================================================
    # INIT
    # =========================================================

    def __init__(
        self,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)

        self.setObjectName(
            "HomePage"
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_StyledBackground,
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

        outer = QHBoxLayout(
            self
        )

        outer.setContentsMargins(
            0,
            0,
            0,
            0
        )

        outer.setSpacing(
            0
        )

        # =====================================================
        # SCROLL AREA
        # =====================================================

        self.scroll = QScrollArea()

        self.scroll.setWidgetResizable(
            True
        )

        self.scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        # =====================================================
        # CONTENT WIDGET
        # =====================================================

        self.content = QWidget()

        self.content.setStyleSheet(
            "background: transparent;"
        )

        self.scroll.setWidget(
            self.content
        )

        # =====================================================
        # MAIN CONTENT LAYOUT
        # =====================================================

        main = QVBoxLayout(
            self.content
        )

        main.setContentsMargins(
            40,
            32,
            40,
            40
        )

        main.setSpacing(
            0
        )

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

        hero_layout.setSpacing(
            0
        )

        hero_layout.addWidget(
            self.hero
        )

        main.addWidget(
            hero_container
        )

        main.addSpacing(
            8
        )

        # =====================================================
        # STUDIOS HEADER
        # =====================================================

        self._build_studios_header(
            main
        )

        main.addSpacing(
            16
        )

        # =====================================================
        # STUDIO CARDS
        # =====================================================

        self._build_studios_row(
            main
        )

        main.addStretch()

        # =====================================================
        # ADD SCROLL AREA
        # =====================================================

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

        # =====================================================
        # INITIAL RIGHT PANEL STATE
        # =====================================================

        self._update_right_panel()

    # =========================================================
    # HEADER
    # =========================================================

    def _build_studios_header(
        self,
        parent
    ):

        row = QHBoxLayout()

        # -----------------------------------------------------
        # TITLE
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # CREATE BUTTON
        # -----------------------------------------------------

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
    # STUDIO CARDS CONTAINER
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

        # Load cards immediately
        self.refresh_studios()

    # =========================================================
    # CONFIG PATH
    # =========================================================

    def get_config_path(self):

        return os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "backend",
                "config",
                "studios.json"
            )
        )

    # =========================================================
    # LOAD STUDIOS
    # =========================================================

    def load_studios(self):

        config_path = self.get_config_path()

        try:

            if not os.path.exists(
                config_path
            ):

                print(
                    "⚠️ studios.json does not exist."
                )

                return []

            with open(
                config_path,
                "r",
                encoding="utf-8"
            ) as f:

                studios = json.load(
                    f
                )

            # -------------------------------------------------
            # SAFETY CHECK
            # -------------------------------------------------

            if not isinstance(
                studios,
                list
            ):

                print(
                    "⚠️ studios.json does not contain a list."
                )

                return []

            print(
                f"📂 Loaded {len(studios)} studios"
            )

            return studios

        except json.JSONDecodeError as e:

            print(
                f"❌ Invalid studios.json: {e}"
            )

            return []

        except Exception as e:

            print(
                f"❌ Could not load studios.json: {e}"
            )

            return []

    # =========================================================
    # REFRESH DASHBOARD
    # =========================================================

    def refresh_studios(self):

        print(
            "🔄 Refreshing studio dashboard..."
        )

        # =====================================================
        # REMOVE EXISTING CARDS
        # =====================================================

        while self.cards_layout.count():

            item = self.cards_layout.takeAt(0)

            widget = item.widget()

            if widget is not None:

                widget.setParent(
                    None
                )

                widget.deleteLater()

        # =====================================================
        # LOAD COMPLETE STUDIO LIST
        # =====================================================

        studios = self.load_studios()

        print(
            f"🏠 Dashboard displaying {len(studios)} studios"
        )

        # =====================================================
        # CREATE CARDS
        # =====================================================

        for studio in studios:

            if not isinstance(
                studio,
                dict
            ):
                continue

            title = studio.get(
                "title",
                "Untitled Studio"
            )

            if not title:
                continue

            # -------------------------------------------------
            # CARD DATA
            # -------------------------------------------------

            card_data = {

                "title": title,

                "time_ago": studio.get(
                    "time_ago",
                    "Just now"
                ),

                "description": studio.get(
                    "description",
                    ""
                ),

                "apps": studio.get(
                    "apps",
                    []
                ),

                "last_used": studio.get(
                    "last_used",
                    "Not yet"
                ),

                "icon_symbol": studio.get(
                    "icon_symbol",
                    "✦"
                ),

                "accent": studio.get(
                    "accent",
                    "#8B5CF6"
                ),

                "studio_type": studio.get(
                    "type",
                    "built_in"
                ),

                "events": studio.get(
                    "events",
                    []
                )
            }

            # -------------------------------------------------
            # CREATE CARD
            # -------------------------------------------------

            card = StudioCard(
                **card_data
            )

            # -------------------------------------------------
            # BUILT-IN STUDIO LAUNCH
            # -------------------------------------------------

            card.launch_clicked.connect(
                self.launch_studio
            )

            # -------------------------------------------------
            # CUSTOM STUDIO - ALL EVENTS
            # -------------------------------------------------

            card.launch_all_requested.connect(
                self.launch_all_events
            )

            # -------------------------------------------------
            # CUSTOM STUDIO - SPECIFIC EVENT
            # -------------------------------------------------

            card.launch_event_requested.connect(
                self.launch_specific_event
            )

            # -------------------------------------------------
            # ADD TO FLOW LAYOUT
            # -------------------------------------------------

            self.cards_layout.addWidget(
                card
            )

        # =====================================================
        # FORCE LAYOUT UPDATE
        # =====================================================

        self.cards_container.updateGeometry()

        self.cards_layout.invalidate()

        self.cards_layout.activate()

        self.cards_container.adjustSize()

        self.cards_layout.activate()

        self.cards_container.update()

        print(
            "✅ Dashboard refresh complete."
        )

    # =========================================================
    # NORMAL STUDIO LAUNCH
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
    # CUSTOM STUDIO - LAUNCH ALL
    # =========================================================

    def launch_all_events(
        self,
        studio_name
    ):

        print(
            f"🚀 Launching ALL events: {studio_name}"
        )

        # IMPORTANT:
        # Do NOT emit studio_selected here.
        #
        # studio_selected opens the workspace/editor.
        #
        # Instead, tell MainWindow to execute
        # the custom studio events.

        self.launch_all_events_requested.emit(
            studio_name
        )

    # =========================================================
    # CUSTOM STUDIO - LAUNCH ONE EVENT
    # =========================================================

    def launch_specific_event(
        self,
        studio_name,
        event
    ):

        event_name = (
            event.get(
                "name",
                "Unnamed Event"
            )
            if isinstance(
                event,
                dict
            )
            else "Invalid Event"
        )

        print(
            f"🎯 Launching event '{event_name}' "
            f"from '{studio_name}'"
        )

        # IMPORTANT:
        # Do NOT emit studio_selected here.
        #
        # Send the event directly to MainWindow.

        self.launch_specific_event_requested.emit(
            studio_name,
            event
        )

    # =========================================================
    # RIGHT PANEL
    # =========================================================

    def _update_right_panel(
        self
    ):

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
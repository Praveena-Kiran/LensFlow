"""
LensFlow - Custom Studio Page

Handles:
- Creating custom studios
- Loading existing studios
- Renaming studios
- Adding/editing/deleting events
- Saving studio configuration
- Deleting custom studios
- Selecting files through Windows File Explorer
"""

import json
import os
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QCompleter
from PySide6.QtGui import QColor, QPainter, QRadialGradient, QBrush, QPen, QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QMessageBox,
    QScrollArea,
    QFrame,
    QDialog,
    QComboBox,
    QFileDialog,
)
from backend.paths import user_config_path
from frontend.styles.theme import (
    BG_DARK,
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
    SUCCESS,
    WARNING,
    ERROR,
)


class _EventIconBadge(QWidget):
    """Refined circular icon badge for action types."""

    ACTION_MAP = {
        "Open Application": ("💻", "#5B8CFF"),
        "Open File": ("📄", "#6875F5"),
        "Open Website": ("🌐", "#5B8CFF"),
        "Hotkey": ("⌨", "#8B70FF"),
        "Wait": ("⏳", "#7C5CFF"),
        "PowerPoint": ("📊", "#6875F5"),
    }

    def __init__(self, action: str = "", size: int = 38, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        icon, color = self.ACTION_MAP.get(action, ("⚡", PRIMARY))
        self._icon = icon
        self._color = QColor(color)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = float(min(self.width(), self.height()))

        # Background tint
        bg = QColor(self._color)
        bg.setAlpha(30)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(bg))
        p.drawEllipse(0, 0, int(s), int(s))

        # Border
        border = QColor(self._color)
        border.setAlpha(80)
        p.setPen(QPen(border, 1.2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(1, 1, int(s - 2), int(s - 2))

        # Icon Symbol
        p.setPen(QColor(self._color).lighter(135))
        font = QFont("Segoe UI Emoji", int(s * 0.36))
        p.setFont(font)
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._icon)


class CustomPage(QWidget):

    # =========================================================
    # SIGNALS
    # =========================================================

    back_requested = Signal()
    studio_saved = Signal()
    studio_deleted = Signal()

    # =========================================================
    # INIT
    # =========================================================

    def __init__(
        self,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)

        self.setObjectName(
            "CustomPage"
        )

        self.current_studio = None
        self.studio_name = ""
        self.events = []

        self.setStyleSheet(f"""
            QWidget#CustomPage {{
                background-color: {BG_DARK};
            }}

            QLabel {{
                color: {PRIMARY_TEXT};
            }}

            QLineEdit,
            QComboBox {{
                background-color: {SURFACE};
                color: {PRIMARY_TEXT};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }}

            QLineEdit:focus,
            QComboBox:focus {{
                border: 1px solid {PRIMARY};
            }}

            QPushButton {{
                background-color: {SURFACE};
                color: {PRIMARY_TEXT};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 7px 14px;
                font-size: 12px;
                font-weight: 500;
            }}

            QPushButton:hover {{
                background-color: {SURFACE_HOVER};
                border: 1px solid rgba(255, 255, 255, 0.16);
            }}
        """)

        self._build_ui()

    # =========================================================
    # CONFIG PATH
    # =========================================================

    def get_config_path(self):

        return user_config_path("studios.json")

    # =========================================================
    # LOAD ALL STUDIOS
    # =========================================================

    def load_all_studios(self):

        path = self.get_config_path()

        try:

            if not os.path.exists(path):

                print(
                    "⚠️ studios.json does not exist."
                )

                return []

            with open(
                path,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

            if not isinstance(data, list):

                print(
                    "⚠️ studios.json must contain a list."
                )

                return []

            print(
                f"📂 Loaded {len(data)} studios from config."
            )

            return data

        except json.JSONDecodeError as e:

            print(
                f"❌ studios.json contains invalid JSON: {e}"
            )

            return []

        except Exception as e:

            print(
                f"❌ Failed to load studios.json: {e}"
            )

            return []

    # =========================================================
    # SAVE ALL STUDIOS
    # =========================================================

    def save_all_studios(
        self,
        studios
    ):

        path = self.get_config_path()

        try:

            os.makedirs(
                os.path.dirname(path),
                exist_ok=True
            )

            with open(
                path,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    studios,
                    file,
                    indent=4,
                    ensure_ascii=False
                )

            print(
                f"💾 Saved {len(studios)} studios to config."
            )

            return True

        except Exception as e:

            print(
                f"❌ Failed to save studios.json: {e}"
            )

            QMessageBox.critical(
                self,
                "Save Error",
                f"Could not save studios.json:\n\n{e}"
            )

            return False

    # =========================================================
    # BUILD UI
    # =========================================================

    def _build_ui(self):

        outer = QVBoxLayout(
            self
        )

        outer.setContentsMargins(
            36,
            24,
            36,
            36
        )

        outer.setSpacing(
            18
        )

        # =====================================================
        # TOP BAR
        # =====================================================

        top = QHBoxLayout()

        back = QPushButton(
            "← Back"
        )
        back.setFixedHeight(34)
        back.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        back.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.04);
                color: {PRIMARY_TEXT};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 0px 14px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.16);
                color: #FFFFFF;
            }}
        """)

        back.clicked.connect(
            self.go_back
        )

        top.addWidget(
            back
        )

        top.addSpacing(
            10
        )

        title = QLabel(
            "Custom Studio"
        )

        title.setStyleSheet(f"""
            color: {PRIMARY_TEXT};
            font-size: 22px;
            font-weight: 700;
            letter-spacing: -0.4px;
        """)

        top.addWidget(
            title
        )

        top.addStretch()

        # -----------------------------------------------------
        # DELETE BUTTON
        # -----------------------------------------------------

        self.delete_button = QPushButton(
            "Delete Studio"
        )
        self.delete_button.setFixedHeight(34)
        self.delete_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.delete_button.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(239, 68, 68, 0.10);
                color: {ERROR};
                border: 1px solid rgba(239, 68, 68, 0.25);
                border-radius: 8px;
                padding: 0px 14px;
                font-size: 12px;
                font-weight: 600;
            }}

            QPushButton:hover {{
                background-color: rgba(239, 68, 68, 0.20);
                border: 1px solid rgba(239, 68, 68, 0.40);
                color: #FCA5A5;
            }}
            QPushButton:pressed {{
                background-color: rgba(239, 68, 68, 0.28);
            }}
        """)

        self.delete_button.clicked.connect(
            self.delete_current_studio
        )

        self.delete_button.hide()

        top.addWidget(
            self.delete_button
        )

        outer.addLayout(
            top
        )

        # =====================================================
        # STUDIO NAME
        # =====================================================

        name_label = QLabel(
            "STUDIO NAME"
        )

        name_label.setStyleSheet(f"""
            font-size: 10px;
            font-weight: 600;
            color: {TEXT_MUTED};
            letter-spacing: 0.5px;
        """)

        outer.addWidget(
            name_label
        )

        name_row = QHBoxLayout()
        name_row.setSpacing(10)

        self.name_input = QLineEdit()
        self.name_input.setFixedHeight(36)
        self.name_input.setPlaceholderText(
            "Enter studio name..."
        )

        name_row.addWidget(
            self.name_input,
            1
        )

        save_name = QPushButton(
            "Save Name"
        )
        save_name.setFixedHeight(36)
        save_name.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        save_name.setStyleSheet(f"""
            QPushButton {{
                background-color: {PRIMARY};
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
                padding: 0px 16px;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {PRIMARY_PRESSED};
            }}
        """)

        save_name.clicked.connect(
            self.save_studio_name
        )

        name_row.addWidget(
            save_name
        )

        outer.addLayout(
            name_row
        )

        outer.addSpacing(6)

        # =====================================================
        # EVENTS HEADER
        # =====================================================

        events_header = QHBoxLayout()

        events_title = QLabel(
            "Events & Automations"
        )

        events_title.setStyleSheet(f"""
            color: {PRIMARY_TEXT};
            font-size: 16px;
            font-weight: 700;
            letter-spacing: -0.2px;
        """)

        events_header.addWidget(
            events_title
        )

        events_header.addStretch()

        add_event = QPushButton(
            "+ Add Event"
        )
        add_event.setFixedHeight(34)
        add_event.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        add_event.setStyleSheet(f"""
            QPushButton {{
                background-color: {PRIMARY};
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
                padding: 0px 14px;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {PRIMARY_PRESSED};
            }}
        """)

        add_event.clicked.connect(
            self.add_event
        )

        events_header.addWidget(
            add_event
        )

        outer.addLayout(
            events_header
        )

        # =====================================================
        # EVENTS SCROLL
        # =====================================================

        self.events_scroll = QScrollArea()

        self.events_scroll.setWidgetResizable(
            True
        )

        self.events_scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.events_content = QWidget()

        self.events_layout = QVBoxLayout(
            self.events_content
        )

        self.events_layout.setContentsMargins(
            0,
            0,
            0,
            20
        )

        self.events_layout.setSpacing(
            12
        )

        self.events_layout.addStretch()

        self.events_scroll.setWidget(
            self.events_content
        )

        outer.addWidget(
            self.events_scroll,
            1
        )

    # =========================================================
    # START NEW STUDIO
    # =========================================================

    def start_new_studio(
        self,
        name
    ):

        name = name.strip()

        if not name:

            QMessageBox.warning(
                self,
                "Invalid Name",
                "Please enter a studio name."
            )

            return False

        studios = self.load_all_studios()

        # -----------------------------------------------------
        # CHECK DUPLICATE
        # -----------------------------------------------------

        for studio in studios:

            existing_name = studio.get(
                "title",
                ""
            ).strip().lower()

            if existing_name == name.lower():

                QMessageBox.warning(
                    self,
                    "Studio Already Exists",
                    f"A studio named '{name}' already exists."
                )

                return False

        # -----------------------------------------------------
        # CREATE STUDIO
        # -----------------------------------------------------

        new_studio = {
            "title": name,
            "time_ago": "Just now",
            "description": "Custom gesture-controlled workspace.",
            "apps": [],
            "last_used": "Not yet",
            "icon_symbol": "✦",
            "accent": "#8B5CF6",
            "type": "custom",
            "events": []
        }

        studios.append(
            new_studio
        )

        if not self.save_all_studios(
            studios
        ):

            return False

        print(
            f"✨ Created custom studio: {name}"
        )

        self.load_studio(
            name
        )

        self.delete_button.show()

        self.studio_saved.emit()

        return True

    # =========================================================
    # LOAD STUDIO
    # =========================================================

    def load_studio(
        self,
        name
    ):

        studios = self.load_all_studios()

        found = None

        for studio in studios:

            title = studio.get(
                "title",
                ""
            ).strip()

            if title.lower() == name.strip().lower():

                found = studio
                break

        if found is None:

            print(
                f"❌ Studio not found: {name}"
            )

            return False

        self.current_studio = found

        self.studio_name = found.get(
            "title",
            ""
        )

        self.events = found.get(
            "events",
            []
        )

        if not isinstance(
            self.events,
            list
        ):

            self.events = []

        self.name_input.setText(
            self.studio_name
        )

        if (
            found.get("type") == "custom"
            or "type" not in found
        ):

            self.delete_button.show()

        else:

            self.delete_button.hide()

        self.refresh_events()

        print(
            f"📂 Loaded studio: {self.studio_name}"
        )

        return True

    # =========================================================
    # FIND CURRENT STUDIO
    # =========================================================

    def find_current_studio(self):

        if not self.studio_name:

            return None

        studios = self.load_all_studios()

        for studio in studios:

            title = studio.get(
                "title",
                ""
            ).strip().lower()

            if title == self.studio_name.strip().lower():

                return studio

        return None

    # =========================================================
    # SAVE CURRENT STUDIO
    # =========================================================

    def save_current_studio(self):

        if not self.studio_name:

            return False

        studios = self.load_all_studios()

        found = False

        for studio in studios:

            title = studio.get(
                "title",
                ""
            ).strip().lower()

            if title == self.studio_name.strip().lower():

                studio["events"] = self.events

                found = True

                break

        if not found:

            print(
                f"⚠️ Could not save studio: {self.studio_name}"
            )

            return False

        return self.save_all_studios(
            studios
        )

    # =========================================================
    # SET STUDIO NAME
    # =========================================================

    def set_studio_name(
        self,
        name
    ):

        self.studio_name = name.strip()

        self.name_input.setText(
            self.studio_name
        )

    # =========================================================
    # SAVE / RENAME STUDIO
    # =========================================================

    def save_studio_name(self):

        new_name = self.name_input.text().strip()

        if not new_name:

            QMessageBox.warning(
                self,
                "Invalid Name",
                "Studio name cannot be empty."
            )

            return

        if not self.studio_name:

            return

        old_name = self.studio_name

        studios = self.load_all_studios()

        # -----------------------------------------------------
        # CHECK DUPLICATE
        # -----------------------------------------------------

        for studio in studios:

            existing = studio.get(
                "title",
                ""
            ).strip().lower()

            if (
                existing == new_name.lower()
                and existing != old_name.lower()
            ):

                QMessageBox.warning(
                    self,
                    "Studio Already Exists",
                    f"A studio named '{new_name}' already exists."
                )

                self.name_input.setText(
                    old_name
                )

                return

        # -----------------------------------------------------
        # RENAME
        # -----------------------------------------------------

        renamed = False

        for studio in studios:

            existing = studio.get(
                "title",
                ""
            ).strip().lower()

            if existing == old_name.lower():

                studio["title"] = new_name

                renamed = True

                break

        if not renamed:

            QMessageBox.warning(
                self,
                "Studio Not Found",
                "Could not find the studio to rename."
            )

            return

        if not self.save_all_studios(
            studios
        ):

            return

        self.studio_name = new_name

        self.current_studio = self.find_current_studio()

        print(
            f"✏️ Renamed studio: {old_name} → {new_name}"
        )

        self.studio_saved.emit()

    # =========================================================
    # ADD EVENT
    # =========================================================

    def add_event(self):

        if not self.studio_name:

            QMessageBox.warning(
                self,
                "No Studio",
                "Please create or select a studio first."
            )

            return

        dialog = EventDialog(
            self
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:

            return

        event = dialog.get_event()

        self.events.append(
            event
        )

        if self.save_current_studio():

            self.refresh_events()

            self.studio_saved.emit()

    # =========================================================
    # EDIT EVENT
    # =========================================================

    def edit_event(
        self,
        index
    ):

        if index < 0 or index >= len(
            self.events
        ):

            return

        dialog = EventDialog(
            self,
            self.events[index]
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:

            return

        self.events[index] = dialog.get_event()

        if self.save_current_studio():

            self.refresh_events()

            self.studio_saved.emit()

    # =========================================================
    # DELETE EVENT
    # =========================================================

    def delete_event(
        self,
        index
    ):

        if index < 0 or index >= len(
            self.events
        ):

            return

        reply = QMessageBox.question(
            self,
            "Delete Event",
            "Are you sure you want to delete this event?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:

            return

        del self.events[index]

        if self.save_current_studio():

            self.refresh_events()

            self.studio_saved.emit()

    # =========================================================
    # REFRESH EVENTS
    # =========================================================

    def refresh_events(self):

        # -----------------------------------------------------
        # REMOVE EXISTING EVENT WIDGETS
        # -----------------------------------------------------

        while self.events_layout.count() > 1:

            item = self.events_layout.takeAt(
                0
            )

            widget = item.widget()

            if widget is not None:

                widget.deleteLater()

        # -----------------------------------------------------
        # EMPTY STATE
        # -----------------------------------------------------

        if not self.events:

            empty = QLabel(
                "No events yet.\n"
                "Click '+ Add Event' to create your first automation."
            )

            empty.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            empty.setMinimumHeight(
                100
            )

            empty.setStyleSheet(f"""
                QLabel {{
                    color: {TEXT_MUTED};
                    background: {SURFACE};
                    border: 1px solid {BORDER};
                    border-radius: 12px;
                    padding: 30px;
                    font-size: 13px;
                }}
            """)

            self.events_layout.insertWidget(
                0,
                empty
            )

            return

        # -----------------------------------------------------
        # CREATE EVENT CARDS
        # -----------------------------------------------------

        for index, event in enumerate(
            self.events
        ):

            card = QFrame()
            card.setObjectName("EventCard")

            card.setStyleSheet(f"""
                QFrame#EventCard {{
                    background-color: {SURFACE};
                    border: 1px solid {BORDER};
                    border-radius: 12px;
                }}
                QFrame#EventCard:hover {{
                    background-color: {SURFACE_HOVER};
                    border: 1px solid rgba(124, 92, 255, 0.35);
                }}
            """)

            card_layout = QHBoxLayout(
                card
            )

            card_layout.setContentsMargins(
                14,
                12,
                14,
                12
            )

            card_layout.setSpacing(
                14
            )

            # -------------------------------------------------
            # ACTION ICON BADGE
            # -------------------------------------------------

            action_type = event.get(
                "action",
                "Unknown"
            )

            badge = _EventIconBadge(
                action_type,
                size=36
            )

            card_layout.addWidget(
                badge,
                0,
                Qt.AlignmentFlag.AlignVCenter
            )

            # -------------------------------------------------
            # INFO COLUMN
            # -------------------------------------------------

            info_col = QVBoxLayout()
            info_col.setSpacing(3)

            # Top: Event Name + Gesture Tag
            name_row = QHBoxLayout()
            name_row.setSpacing(8)

            event_name = QLabel(
                event.get(
                    "name",
                    "Unnamed Event"
                )
            )

            event_name.setStyleSheet(f"""
                color: {PRIMARY_TEXT};
                font-size: 14px;
                font-weight: 600;
                border: none;
                background: transparent;
            """)

            name_row.addWidget(
                event_name
            )

            gesture = event.get(
                "gesture",
                ""
            )

            if gesture:
                gesture_pill = QLabel(
                    gesture
                )
                gesture_pill.setStyleSheet(f"""
                    color: {WARNING};
                    background-color: rgba(245, 158, 11, 0.12);
                    border: 1px solid rgba(245, 158, 11, 0.25);
                    border-radius: 4px;
                    font-size: 10px;
                    font-weight: 600;
                    padding: 1px 6px;
                """)
                name_row.addWidget(
                    gesture_pill
                )

            name_row.addStretch()
            info_col.addLayout(
                name_row
            )

            # Action subtitle
            action_label = QLabel(
                action_type
            )

            action_label.setStyleSheet(f"""
                color: {SECONDARY_TEXT};
                font-size: 11px;
                font-weight: 500;
                border: none;
                background: transparent;
            """)

            info_col.addWidget(
                action_label
            )

            # Value with truncation & tooltip
            value = str(
                event.get(
                    "value",
                    ""
                )
            )

            if value:
                if len(value) > 50:
                    if "/" in value or "\\" in value:
                        parts = value.replace("\\", "/").split("/")
                        display_val = f".../{parts[-1]}" if parts[-1] else value[:45] + "..."
                    else:
                        display_val = value[:45] + "..."
                else:
                    display_val = value

                value_label = QLabel(
                    display_val
                )
                value_label.setToolTip(
                    value
                )
                value_label.setStyleSheet(f"""
                    color: {TEXT_MUTED};
                    font-size: 11px;
                    font-family: "Consolas", "Courier New", monospace;
                    border: none;
                    background: transparent;
                """)
                info_col.addWidget(
                    value_label
                )

            card_layout.addLayout(
                info_col,
                1
            )

            # -------------------------------------------------
            # ACTION BUTTONS
            # -------------------------------------------------

            buttons = QHBoxLayout()
            buttons.setSpacing(6)

            edit_button = QPushButton(
                "Edit"
            )
            edit_button.setFixedHeight(28)
            edit_button.setCursor(
                Qt.CursorShape.PointingHandCursor
            )
            edit_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(255, 255, 255, 0.04);
                    color: {PRIMARY_TEXT};
                    border: 1px solid {BORDER};
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: 500;
                    padding: 0px 10px;
                }}
                QPushButton:hover {{
                    background-color: rgba(255, 255, 255, 0.08);
                    border: 1px solid rgba(255, 255, 255, 0.16);
                    color: #FFFFFF;
                }}
            """)

            edit_button.clicked.connect(
                lambda checked=False, i=index:
                self.edit_event(i)
            )

            buttons.addWidget(
                edit_button
            )

            delete_button = QPushButton(
                "Delete"
            )
            delete_button.setFixedHeight(28)
            delete_button.setCursor(
                Qt.CursorShape.PointingHandCursor
            )

            delete_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(239, 68, 68, 0.08);
                    color: {ERROR};
                    border: 1px solid rgba(239, 68, 68, 0.20);
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: 500;
                    padding: 0px 10px;
                }}

                QPushButton:hover {{
                    background-color: rgba(239, 68, 68, 0.18);
                    border: 1px solid rgba(239, 68, 68, 0.35);
                    color: #FCA5A5;
                }}
            """)

            delete_button.clicked.connect(
                lambda checked=False, i=index:
                self.delete_event(i)
            )

            buttons.addWidget(
                delete_button
            )

            card_layout.addLayout(
                buttons
            )

            self.events_layout.insertWidget(
                index,
                card
            )

    # =========================================================
    # DELETE CURRENT STUDIO
    # =========================================================

    def delete_current_studio(self):

        if not self.studio_name:

            return

        studios = self.load_all_studios()

        current = None

        for studio in studios:

            title = studio.get(
                "title",
                ""
            ).strip().lower()

            if title == self.studio_name.strip().lower():

                current = studio
                break

        if current is None:

            QMessageBox.warning(
                self,
                "Studio Not Found",
                "The selected studio could not be found."
            )

            return

        # -----------------------------------------------------
        # ONLY CUSTOM STUDIOS
        # -----------------------------------------------------

        studio_type = current.get(
            "type"
        )

        if (
            studio_type is not None
            and studio_type != "custom"
        ):

            QMessageBox.warning(
                self,
                "Cannot Delete Studio",
                "Built-in studios cannot be deleted."
            )

            return

        # -----------------------------------------------------
        # CONFIRM
        # -----------------------------------------------------

        reply = QMessageBox.question(
            self,
            "Delete Studio",
            (
                f"Are you sure you want to delete "
                f"'{self.studio_name}'?\n\n"
                "This will permanently remove this custom studio."
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:

            return

        # -----------------------------------------------------
        # REMOVE ONLY CURRENT STUDIO
        # -----------------------------------------------------

        old_name = self.studio_name.strip().lower()

        updated_studios = []

        deleted = False

        for studio in studios:

            title = studio.get(
                "title",
                ""
            ).strip().lower()

            if title == old_name:

                deleted = True

                print(
                    f"🗑️ Removing studio: {studio.get('title')}"
                )

                continue

            updated_studios.append(
                studio
            )

        if not deleted:

            print(
                "⚠️ Delete failed: studio was not found."
            )

            return

        # -----------------------------------------------------
        # SAVE COMPLETE REMAINING LIST
        # -----------------------------------------------------

        if not self.save_all_studios(
            updated_studios
        ):

            return

        print(
            f"✅ Deleted studio: {self.studio_name}"
        )

        print(
            f"📂 Remaining studios: {len(updated_studios)}"
        )

        # -----------------------------------------------------
        # CLEAR PAGE
        # -----------------------------------------------------

        self.current_studio = None
        self.studio_name = ""
        self.events = []

        self.name_input.clear()

        self.delete_button.hide()

        self.refresh_events()

        # -----------------------------------------------------
        # NOTIFY MAIN WINDOW
        # -----------------------------------------------------

        self.studio_deleted.emit()

        self.studio_saved.emit()

        self.back_requested.emit()

    # =========================================================
    # BACK
    # =========================================================

    def go_back(self):

        self.back_requested.emit()


# =============================================================
# EVENT DIALOG
# =============================================================

class EventDialog(QDialog):

    def __init__(
        self,
        parent=None,
        event=None
    ):

        super().__init__(
            parent
        )

        self.setWindowTitle(
            "Event Configuration"
        )

        self.setMinimumWidth(
            520
        )

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}

            QLabel {{
                color: {PRIMARY_TEXT};
                font-size: 12px;
                font-weight: 600;
            }}

            QLineEdit,
            QComboBox {{
                background-color: {BG_DARK};
                color: {PRIMARY_TEXT};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }}

            QLineEdit:focus,
            QComboBox:focus {{
                border: 1px solid {PRIMARY};
            }}

            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
        """)

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            24,
            24,
            24,
            24
        )

        layout.setSpacing(
            12
        )

        # =====================================================
        # EVENT NAME
        # =====================================================

        layout.addWidget(
            QLabel(
                "Event Name"
            )
        )

        self.name_input = QLineEdit()
        self.name_input.setFixedHeight(36)
        self.name_input.setPlaceholderText(
            "Example: Open VS Code"
        )

        layout.addWidget(
            self.name_input
        )

        # =====================================================
        # GESTURE
        # =====================================================

        layout.addWidget(
            QLabel(
                "Gesture Trigger (Optional)"
            )
        )

        self.gesture_input = QLineEdit()
        self.gesture_input.setFixedHeight(36)
        self.gesture_input.setPlaceholderText(
            "Start typing, e.g. ✋ Open Palm or one of your gestures"
        )

        # Suggest built-in gestures and the user's recorded ones.
        try:
            from backend.gestures.custom_gestures import CustomGestureStore
            from backend.gestures.google_gesture_recognizer import (
                BUILTIN_GESTURE_NAMES,
            )

            suggestions = (
                list(BUILTIN_GESTURE_NAMES)
                + CustomGestureStore().names()
            )

        except Exception as e:
            print(f"⚠ Could not load gesture suggestions: {e}")
            suggestions = []

        completer = QCompleter(suggestions, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)

        self.gesture_input.setCompleter(completer)

        layout.addWidget(
            self.gesture_input
        )

        # =====================================================
        # ACTION
        # =====================================================

        layout.addWidget(
            QLabel(
                "Action Type"
            )
        )

        self.action_combo = QComboBox()
        self.action_combo.setFixedHeight(36)

        self.action_combo.addItems([
            "Open Application",
            "Open File",
            "Open Website",
            "Hotkey",
            "Wait",
            "PowerPoint"
        ])

        layout.addWidget(
            self.action_combo
        )

        # =====================================================
        # VALUE + FILE EXPLORER
        # =====================================================

        layout.addWidget(
            QLabel(
                "Target Value / Path"
            )
        )

        value_row = QHBoxLayout()
        value_row.setSpacing(8)

        self.value_input = QLineEdit()
        self.value_input.setFixedHeight(36)
        self.value_input.setPlaceholderText(
            "Application path, file path, URL, hotkey, etc."
        )

        value_row.addWidget(
            self.value_input,
            1
        )

        self.browse_button = QPushButton(
            "📁 Browse"
        )
        self.browse_button.setFixedHeight(36)
        self.browse_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.browse_button.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.04);
                color: {PRIMARY_TEXT};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 0px 14px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.16);
            }}
        """)

        self.browse_button.clicked.connect(
            self.browse_file
        )

        value_row.addWidget(
            self.browse_button
        )

        layout.addLayout(
            value_row
        )

        # =====================================================
        # HINT
        # =====================================================

        self.file_hint = QLabel(
            "Browse lets you select a file or application directly from Windows File Explorer."
        )

        self.file_hint.setWordWrap(
            True
        )

        self.file_hint.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_MUTED};
                font-size: 11px;
                border: none;
                background: transparent;
            }}
        """)

        layout.addWidget(
            self.file_hint
        )

        layout.addSpacing(6)

        # =====================================================
        # BUTTONS
        # =====================================================

        buttons = QHBoxLayout()
        buttons.setSpacing(10)

        buttons.addStretch()

        cancel = QPushButton(
            "Cancel"
        )
        cancel.setFixedHeight(34)
        cancel.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.04);
                color: {SECONDARY_TEXT};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 0px 16px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.16);
                color: {PRIMARY_TEXT};
            }}
        """)

        cancel.clicked.connect(
            self.reject
        )

        save = QPushButton(
            "Save Event"
        )
        save.setFixedHeight(34)
        save.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        save.setStyleSheet(f"""
            QPushButton {{
                background-color: {PRIMARY};
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
                padding: 0px 18px;
            }}

            QPushButton:hover {{
                background-color: {PRIMARY_HOVER};
            }}

            QPushButton:pressed {{
                background-color: {PRIMARY_PRESSED};
            }}
        """)

        save.clicked.connect(
            self.save_event
        )

        buttons.addWidget(
            cancel
        )

        buttons.addWidget(
            save
        )

        layout.addLayout(
            buttons
        )

        # =====================================================
        # LOAD EXISTING EVENT
        # =====================================================

        if event:

            self.name_input.setText(
                event.get(
                    "name",
                    ""
                )
            )

            self.gesture_input.setText(
                event.get(
                    "gesture",
                    ""
                )
            )

            action = event.get(
                "action",
                ""
            )

            action_index = self.action_combo.findText(
                action
            )

            if action_index >= 0:

                self.action_combo.setCurrentIndex(
                    action_index
                )

            self.value_input.setText(
                str(
                    event.get(
                        "value",
                        ""
                    )
                )
            )

    # =========================================================
    # BROWSE FILE
    # =========================================================

    def browse_file(self):

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "",
            (
                "All Files (*.*);;"
                "Applications (*.exe *.bat *.cmd);;"
                "Python Files (*.py);;"
                "Documents (*.pdf *.doc *.docx *.txt);;"
                "Images (*.png *.jpg *.jpeg *.gif);;"
                "Videos (*.mp4 *.avi *.mkv)"
            )
        )

        if not file_path:

            return

        self.value_input.setText(
            file_path
        )

        print(
            f"📁 Selected file: {file_path}"
        )

    # =========================================================
    # SAVE EVENT
    # =========================================================

    def save_event(self):

        name = self.name_input.text().strip()

        action = self.action_combo.currentText()

        value = self.value_input.text().strip()

        gesture = self.gesture_input.text().strip()

        # -----------------------------------------------------
        # VALIDATION
        # -----------------------------------------------------

        if not name:

            QMessageBox.warning(
                self,
                "Missing Event Name",
                "Please enter an event name."
            )

            return

        if not value:

            QMessageBox.warning(
                self,
                "Missing Value",
                "Please enter a value or select a file."
            )

            return

        self.accept()

    # =========================================================
    # GET EVENT
    # =========================================================

    def get_event(self):

        return {
            "name": self.name_input.text().strip(),
            "gesture": self.gesture_input.text().strip(),
            "action": self.action_combo.currentText(),
            "value": self.value_input.text().strip()
        }
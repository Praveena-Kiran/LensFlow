"""
LensFlow - Custom Studio Page

Allows users to:
    - Create and edit custom gesture-controlled studios
    - Add, edit and delete events
    - Assign gestures to actions
    - Persist studio events inside backend/config/studios.json
    - Delete custom studios without affecting other studios
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
    QPushButton,
    QFrame,
    QDialog,
    QLineEdit,
    QComboBox,
    QDialogButtonBox,
    QMessageBox,
)


class CustomPage(QWidget):

    # ---------------------------------------------------------
    # Signals
    # ---------------------------------------------------------

    back_requested = Signal()

    # ---------------------------------------------------------
    # Constructor
    # ---------------------------------------------------------

    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)

        self.setObjectName("CustomPage")

        self.setAttribute(
            Qt.WA_StyledBackground,
            True
        )

        # Current studio
        self.studio_name = ""

        # Current studio's events
        self.custom_events = []

        # -----------------------------------------------------
        # Styling
        # -----------------------------------------------------

        self.setStyleSheet("""
            QWidget#CustomPage {
                background-color: #0B0B0F;
            }

            QFrame#ContentFrame {
                background-color: #16161E;
                border-radius: 16px;
            }

            QFrame#EventCard {
                background-color: #20202A;
                border: 1px solid #30303D;
                border-radius: 12px;
            }

            QFrame#EventCard:hover {
                border: 1px solid #3B82F6;
            }
        """)

        # -----------------------------------------------------
        # Main layout
        # -----------------------------------------------------

        main = QVBoxLayout(self)

        main.setContentsMargins(
            40,
            32,
            40,
            32
        )

        main.setSpacing(24)

        # =====================================================
        # HEADER
        # =====================================================

        header = QHBoxLayout()

        left = QVBoxLayout()

        left.setSpacing(5)

        # -----------------------------------------------------
        # Back button
        # -----------------------------------------------------

        back_button = QPushButton(
            "← Back"
        )

        back_button.setCursor(
            Qt.PointingHandCursor
        )

        back_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #60A5FA;
                font-size: 13px;
                font-weight: 600;
                text-align: left;
            }

            QPushButton:hover {
                color: #93C5FD;
            }
        """)

        back_button.clicked.connect(
            self.back_requested.emit
        )

        left.addWidget(
            back_button,
            0,
            Qt.AlignLeft
        )

        # -----------------------------------------------------
        # Studio title
        # -----------------------------------------------------

        self.title_label = QLabel(
            "Custom Studio"
        )

        self.title_label.setStyleSheet("""
            color: white;
            font-size: 28px;
            font-weight: 700;
        """)

        left.addWidget(
            self.title_label
        )

        # -----------------------------------------------------
        # Subtitle
        # -----------------------------------------------------

        self.subtitle_label = QLabel(
            "Create your own gesture-controlled workspace."
        )

        self.subtitle_label.setStyleSheet("""
            color: #9CA3AF;
            font-size: 14px;
        """)

        left.addWidget(
            self.subtitle_label
        )

        header.addLayout(left)

        header.addStretch()

        # -----------------------------------------------------
        # Delete studio button
        # -----------------------------------------------------

        self.delete_studio_button = QPushButton(
            "Delete Studio"
        )

        self.delete_studio_button.setCursor(
            Qt.PointingHandCursor
        )

        self.delete_studio_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #F87171;
                border: 1px solid #7F1D1D;
                border-radius: 9px;
                padding: 8px 14px;
                font-size: 12px;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #3A1518;
                border: 1px solid #EF4444;
            }
        """)

        self.delete_studio_button.clicked.connect(
            self.delete_current_studio
        )

        header.addWidget(
            self.delete_studio_button,
            0,
            Qt.AlignTop
        )

        main.addLayout(
            header
        )

        # =====================================================
        # CONTENT FRAME
        # =====================================================

        content_frame = QFrame()

        content_frame.setObjectName(
            "ContentFrame"
        )

        content_layout = QVBoxLayout(
            content_frame
        )

        content_layout.setContentsMargins(
            24,
            24,
            24,
            24
        )

        content_layout.setSpacing(18)

        # -----------------------------------------------------
        # Events header
        # -----------------------------------------------------

        events_header = QHBoxLayout()

        events_label = QLabel(
            "Your Events"
        )

        events_label.setStyleSheet("""
            color: white;
            font-size: 18px;
            font-weight: 600;
        """)

        events_header.addWidget(
            events_label
        )

        events_header.addStretch()

        # Add event button

        add_event_button = QPushButton(
            "+ Add Event"
        )

        add_event_button.setCursor(
            Qt.PointingHandCursor
        )

        add_event_button.setStyleSheet("""
            QPushButton {
                background: #2563EB;
                color: white;
                border: none;
                border-radius: 9px;
                padding: 9px 16px;
                font-size: 13px;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #3B82F6;
            }

            QPushButton:pressed {
                background: #1D4ED8;
            }
        """)

        add_event_button.clicked.connect(
            self.open_add_event_dialog
        )

        events_header.addWidget(
            add_event_button
        )

        content_layout.addLayout(
            events_header
        )

        # -----------------------------------------------------
        # Events container
        # -----------------------------------------------------

        self.events_layout = QVBoxLayout()

        self.events_layout.setSpacing(
            12
        )

        content_layout.addLayout(
            self.events_layout
        )

        # -----------------------------------------------------
        # Empty state
        # -----------------------------------------------------

        self.empty_label = QLabel(
            "No custom events yet.\n"
            "Add an event to start building this workspace."
        )

        self.empty_label.setStyleSheet("""
            color: #9CA3AF;
            font-size: 14px;
            padding: 12px 0;
        """)

        self.events_layout.addWidget(
            self.empty_label
        )

        content_layout.addStretch()

        main.addWidget(
            content_frame,
            1
        )

        # =====================================================
        # STATUS
        # =====================================================

        self.status = QLabel(
            "Status: Ready"
        )

        self.status.setStyleSheet("""
            color: #9CA3AF;
            font-size: 12px;
        """)

        main.addWidget(
            self.status
        )

        # -----------------------------------------------------
        # Default state
        # -----------------------------------------------------

        self.delete_studio_button.hide()

    # =========================================================
    # FILE PATH
    # =========================================================

    def get_config_path(self):

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

        return config_path

    # =========================================================
    # SET STUDIO
    # =========================================================

    def set_studio_name(
        self,
        name
    ):

        self.studio_name = name

        self.title_label.setText(
            name
        )

        self.subtitle_label.setText(
            "Create and customize your gesture-controlled workspace."
        )

        # -----------------------------------------------------
        # Load this studio's events
        # -----------------------------------------------------

        self.load_current_studio()

        # -----------------------------------------------------
        # Determine whether this is custom
        # -----------------------------------------------------

        studio = self.find_current_studio()

        if studio is not None:

            studio_type = studio.get(
                "type",
                "builtin"
            )

            if studio_type == "custom":

                self.delete_studio_button.show()

            else:

                self.delete_studio_button.hide()

    # =========================================================
    # FIND CURRENT STUDIO
    # =========================================================

    def find_current_studio(self):

        studios = self.load_all_studios()

        for studio in studios:

            if studio.get("title") == self.studio_name:

                return studio

        return None

    # =========================================================
    # LOAD ALL STUDIOS
    # =========================================================

    def load_all_studios(self):

        config_path = self.get_config_path()

        try:

            with open(
                config_path,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

            if not isinstance(data, list):

                return []

            return data

        except Exception as e:

            print(
                f"❌ Could not load studios.json: {e}"
            )

            return []

    # =========================================================
    # LOAD CURRENT STUDIO
    # =========================================================

    def load_current_studio(self):

        studios = self.load_all_studios()

        current_studio = None

        for studio in studios:

            if studio.get("title") == self.studio_name:

                current_studio = studio
                break

        if current_studio is None:

            self.custom_events = []

            self.refresh_events()

            return

        # -----------------------------------------------------
        # IMPORTANT:
        #
        # Only load THIS studio's events.
        # We do NOT replace the entire studios list.
        # -----------------------------------------------------

        self.custom_events = list(
            current_studio.get(
                "events",
                []
            )
        )

        self.refresh_events()

        print(
            f"✅ Loaded studio: {self.studio_name}"
        )

    # =========================================================
    # SAVE CURRENT STUDIO
    # =========================================================

    def save_current_studio(self):

        if not self.studio_name:

            return False

        config_path = self.get_config_path()

        studios = self.load_all_studios()

        found = False

        # -----------------------------------------------------
        # Find ONLY current studio
        # -----------------------------------------------------

        for studio in studios:

            if studio.get("title") == self.studio_name:

                studio["events"] = list(
                    self.custom_events
                )

                studio["type"] = "custom"

                found = True

                break

        if not found:

            print(
                f"⚠ Could not find studio: {self.studio_name}"
            )

            return False

        # -----------------------------------------------------
        # Save ENTIRE list back
        #
        # This preserves every other studio.
        # -----------------------------------------------------

        try:

            with open(
                config_path,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    studios,
                    f,
                    indent=4,
                    ensure_ascii=False
                )

            print(
                f"✅ Saved studio: {self.studio_name}"
            )

            return True

        except Exception as e:

            print(
                f"❌ Could not save studio: {e}"
            )

            return False

    # =========================================================
    # ADD EVENT
    # =========================================================

    def open_add_event_dialog(self):

        if not self.studio_name:

            self.status.setText(
                "Status: No studio selected."
            )

            return

        dialog = QDialog(
            self
        )

        dialog.setWindowTitle(
            "Create New Event"
        )

        dialog.setMinimumWidth(
            440
        )

        dialog.setStyleSheet("""
            QDialog {
                background: #16161E;
            }

            QLabel {
                color: white;
                font-size: 13px;
            }

            QLineEdit,
            QComboBox {
                background: #20202A;
                color: white;
                border: 1px solid #363646;
                border-radius: 8px;
                padding: 9px;
                font-size: 13px;
            }

            QLineEdit:focus,
            QComboBox:focus {
                border: 1px solid #3B82F6;
            }

            QComboBox QAbstractItemView {
                background: #20202A;
                color: white;
                selection-background-color: #2563EB;
            }

            QDialogButtonBox QPushButton {
                background: #2563EB;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
            }

            QDialogButtonBox QPushButton:hover {
                background: #3B82F6;
            }
        """)

        layout = QVBoxLayout(
            dialog
        )

        layout.setContentsMargins(
            24,
            24,
            24,
            24
        )

        layout.setSpacing(
            10
        )

        # =====================================================
        # EVENT NAME
        # =====================================================

        name_label = QLabel(
            "Event Name"
        )

        layout.addWidget(
            name_label
        )

        name_input = QLineEdit()

        name_input.setPlaceholderText(
            "e.g. Open GitHub"
        )

        layout.addWidget(
            name_input
        )

        layout.addSpacing(
            8
        )

        # =====================================================
        # GESTURE
        # =====================================================

        gesture_label = QLabel(
            "Gesture"
        )

        layout.addWidget(
            gesture_label
        )

        gesture_combo = QComboBox()

        gesture_combo.addItems([
            "✋ Open Palm",
            "✊ Fist",
            "👍 Thumbs Up",
            "👎 Thumbs Down",
        ])

        layout.addWidget(
            gesture_combo
        )

        layout.addSpacing(
            8
        )

        # =====================================================
        # ACTION
        # =====================================================

        action_label = QLabel(
            "Action"
        )

        layout.addWidget(
            action_label
        )

        action_combo = QComboBox()

        action_combo.addItems([
            "Launch Application",
            "Open Website",
            "Hotkey",
            "Wait",
            "PowerPoint",
        ])

        layout.addWidget(
            action_combo
        )

        layout.addSpacing(
            16
        )

        # =====================================================
        # BUTTONS
        # =====================================================

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Ok
        )

        buttons.accepted.connect(
            dialog.accept
        )

        buttons.rejected.connect(
            dialog.reject
        )

        layout.addWidget(
            buttons
        )

        # =====================================================
        # RESULT
        # =====================================================

        if dialog.exec() != QDialog.DialogCode.Accepted:

            return

        event_name = name_input.text().strip()

        gesture = gesture_combo.currentText()

        action = action_combo.currentText()

        if not event_name:

            self.status.setText(
                "Status: Event name is required."
            )

            return

        # -----------------------------------------------------
        # Create event
        # -----------------------------------------------------

        event = {
            "name": event_name,
            "gesture": gesture,
            "action": action,
        }

        self.custom_events.append(
            event
        )

        # -----------------------------------------------------
        # Save ONLY current studio
        # -----------------------------------------------------

        if self.save_current_studio():

            self.refresh_events()

            self.status.setText(
                f"Status: Created '{event_name}'"
            )

        else:

            # Undo in-memory change if save failed

            self.custom_events.remove(
                event
            )

            self.status.setText(
                "Status: Could not save event."
            )

    # =========================================================
    # EDIT EVENT
    # =========================================================

    def edit_event(
        self,
        event
    ):

        dialog = QDialog(
            self
        )

        dialog.setWindowTitle(
            "Edit Event"
        )

        dialog.setMinimumWidth(
            440
        )

        dialog.setStyleSheet("""
            QDialog {
                background: #16161E;
            }

            QLabel {
                color: white;
                font-size: 13px;
            }

            QLineEdit,
            QComboBox {
                background: #20202A;
                color: white;
                border: 1px solid #363646;
                border-radius: 8px;
                padding: 9px;
                font-size: 13px;
            }

            QLineEdit:focus,
            QComboBox:focus {
                border: 1px solid #3B82F6;
            }

            QComboBox QAbstractItemView {
                background: #20202A;
                color: white;
                selection-background-color: #2563EB;
            }

            QDialogButtonBox QPushButton {
                background: #2563EB;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
            }

            QDialogButtonBox QPushButton:hover {
                background: #3B82F6;
            }
        """)

        layout = QVBoxLayout(
            dialog
        )

        layout.setContentsMargins(
            24,
            24,
            24,
            24
        )

        layout.setSpacing(
            10
        )

        # =====================================================
        # EVENT NAME
        # =====================================================

        layout.addWidget(
            QLabel("Event Name")
        )

        name_input = QLineEdit(
            event.get(
                "name",
                ""
            )
        )

        layout.addWidget(
            name_input
        )

        layout.addSpacing(
            8
        )

        # =====================================================
        # GESTURE
        # =====================================================

        layout.addWidget(
            QLabel("Gesture")
        )

        gesture_combo = QComboBox()

        gesture_combo.addItems([
            "✋ Open Palm",
            "✊ Fist",
            "👍 Thumbs Up",
            "👎 Thumbs Down",
        ])

        current_gesture = event.get(
            "gesture",
            "✋ Open Palm"
        )

        index = gesture_combo.findText(
            current_gesture
        )

        if index >= 0:

            gesture_combo.setCurrentIndex(
                index
            )

        layout.addWidget(
            gesture_combo
        )

        layout.addSpacing(
            8
        )

        # =====================================================
        # ACTION
        # =====================================================

        layout.addWidget(
            QLabel("Action")
        )

        action_combo = QComboBox()

        action_combo.addItems([
            "Launch Application",
            "Open Website",
            "Hotkey",
            "Wait",
            "PowerPoint",
        ])

        current_action = event.get(
            "action",
            "Launch Application"
        )

        index = action_combo.findText(
            current_action
        )

        if index >= 0:

            action_combo.setCurrentIndex(
                index
            )

        layout.addWidget(
            action_combo
        )

        layout.addSpacing(
            16
        )

        # =====================================================
        # BUTTONS
        # =====================================================

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Ok
        )

        buttons.accepted.connect(
            dialog.accept
        )

        buttons.rejected.connect(
            dialog.reject
        )

        layout.addWidget(
            buttons
        )

        # =====================================================
        # RESULT
        # =====================================================

        if dialog.exec() != QDialog.DialogCode.Accepted:

            return

        new_name = name_input.text().strip()

        if not new_name:

            self.status.setText(
                "Status: Event name is required."
            )

            return

        # Save old values
        old_event = event.copy()

        # Update event
        event["name"] = new_name

        event["gesture"] = (
            gesture_combo.currentText()
        )

        event["action"] = (
            action_combo.currentText()
        )

        # -----------------------------------------------------
        # Save
        # -----------------------------------------------------

        if self.save_current_studio():

            self.refresh_events()

            self.status.setText(
                f"Status: Updated '{new_name}'"
            )

        else:

            event.clear()

            event.update(
                old_event
            )

            self.status.setText(
                "Status: Could not save changes."
            )

    # =========================================================
    # REFRESH EVENTS
    # =========================================================

    def refresh_events(self):

        # -----------------------------------------------------
        # Remove old widgets
        # -----------------------------------------------------

        while self.events_layout.count():

            item = self.events_layout.takeAt(
                0
            )

            widget = item.widget()

            if widget is not None:

                widget.deleteLater()

        # -----------------------------------------------------
        # Empty state
        # -----------------------------------------------------

        if not self.custom_events:

            self.events_layout.addWidget(
                self.empty_label
            )

            return

        # -----------------------------------------------------
        # Event cards
        # -----------------------------------------------------

        for event in self.custom_events:

            self.create_event_card(
                event
            )

    # =========================================================
    # CREATE EVENT CARD
    # =========================================================

    def create_event_card(
        self,
        event
    ):

        card = QFrame()

        card.setObjectName(
            "EventCard"
        )

        card_layout = QHBoxLayout(
            card
        )

        card_layout.setContentsMargins(
            16,
            14,
            16,
            14
        )

        card_layout.setSpacing(
            12
        )

        # -----------------------------------------------------
        # Information
        # -----------------------------------------------------

        info = QVBoxLayout()

        info.setSpacing(
            4
        )

        name = QLabel(
            event.get(
                "name",
                "Unnamed Event"
            )
        )

        name.setStyleSheet("""
            color: white;
            font-size: 15px;
            font-weight: 600;
        """)

        info.addWidget(
            name
        )

        details = QLabel(
            f'{event.get("gesture", "")}'
            f'  →  '
            f'{event.get("action", "")}'
        )

        details.setStyleSheet("""
            color: #9CA3AF;
            font-size: 13px;
        """)

        info.addWidget(
            details
        )

        card_layout.addLayout(
            info
        )

        card_layout.addStretch()

        # -----------------------------------------------------
        # Edit button
        # -----------------------------------------------------

        edit_button = QPushButton(
            "Edit"
        )

        edit_button.setCursor(
            Qt.PointingHandCursor
        )

        edit_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #60A5FA;
                border: none;
                font-size: 12px;
                font-weight: 600;
                padding: 5px 8px;
            }

            QPushButton:hover {
                color: #93C5FD;
            }
        """)

        edit_button.clicked.connect(
            lambda checked=False,
            current_event=event:
                self.edit_event(
                    current_event
                )
        )

        card_layout.addWidget(
            edit_button
        )

        # -----------------------------------------------------
        # Delete button
        # -----------------------------------------------------

        delete_button = QPushButton(
            "Delete"
        )

        delete_button.setCursor(
            Qt.PointingHandCursor
        )

        delete_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #9CA3AF;
                border: none;
                font-size: 12px;
                padding: 5px 8px;
            }

            QPushButton:hover {
                color: #F87171;
            }
        """)

        delete_button.clicked.connect(
            lambda checked=False,
            current_event=event:
                self.delete_event(
                    current_event
                )
        )

        card_layout.addWidget(
            delete_button
        )

        self.events_layout.addWidget(
            card
        )

    # =========================================================
    # DELETE EVENT
    # =========================================================

    def delete_event(
        self,
        event
    ):

        event_name = event.get(
            "name",
            "this event"
        )

        reply = QMessageBox.question(
            self,
            "Delete Event",
            f"Are you sure you want to delete "
            f"'{event_name}'?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:

            return

        if event not in self.custom_events:

            return

        # -----------------------------------------------------
        # Remove ONLY this event
        # -----------------------------------------------------

        self.custom_events.remove(
            event
        )

        # -----------------------------------------------------
        # Save current studio
        # -----------------------------------------------------

        if self.save_current_studio():

            self.refresh_events()

            self.status.setText(
                f"Status: Deleted '{event_name}'"
            )

        else:

            # Restore event if save failed

            self.custom_events.append(
                event
            )

            self.refresh_events()

            self.status.setText(
                "Status: Could not delete event."
            )

    # =========================================================
    # DELETE CURRENT STUDIO
    # =========================================================

    def delete_current_studio(self):

        if not self.studio_name:

            return

        studio = self.find_current_studio()

        if studio is None:

            return

        # -----------------------------------------------------
        # Prevent deleting built-in studios
        # -----------------------------------------------------

        if studio.get(
            "type",
            "builtin"
        ) != "custom":

            QMessageBox.information(
                self,
                "Built-in Studio",
                "Built-in LensFlow studios cannot be deleted."
            )

            return

        # -----------------------------------------------------
        # Confirmation
        # -----------------------------------------------------

        reply = QMessageBox.question(
            self,
            "Delete Studio",
            f"Are you sure you want to delete "
            f"'{self.studio_name}'?\n\n"
            f"All events inside this studio will also "
            f"be removed.",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:

            return

        config_path = self.get_config_path()

        studios = self.load_all_studios()

        # -----------------------------------------------------
        # IMPORTANT:
        #
        # Remove ONLY the selected studio.
        # -----------------------------------------------------

        updated_studios = [
            studio
            for studio in studios
            if studio.get("title") != self.studio_name
        ]

        # Safety check
        if len(updated_studios) == len(studios):

            self.status.setText(
                "Status: Studio could not be found."
            )

            return

        # -----------------------------------------------------
        # Save remaining studios
        # -----------------------------------------------------

        try:

            with open(
                config_path,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    updated_studios,
                    f,
                    indent=4,
                    ensure_ascii=False
                )

            deleted_name = self.studio_name

            print(
                f"🗑️ Deleted studio: {deleted_name}"
            )

            # -------------------------------------------------
            # Clear current studio
            # -------------------------------------------------

            self.studio_name = ""

            self.custom_events = []

            self.title_label.setText(
                "Custom Studio"
            )

            self.subtitle_label.setText(
                "Create your own gesture-controlled workspace."
            )

            self.delete_studio_button.hide()

            self.refresh_events()

            self.status.setText(
                f"Status: Deleted '{deleted_name}'"
            )

            # -------------------------------------------------
            # Go home
            # -------------------------------------------------

            self.back_requested.emit()

        except Exception as e:

            print(
                f"❌ Could not delete studio: {e}"
            )

            self.status.setText(
                "Status: Could not delete studio."
            )

    # =========================================================
    # SAVE STUDIO NAME
    # =========================================================

    def save_studio_name(
        self,
        new_name
    ):

        new_name = new_name.strip()

        if not new_name:

            return False

        if not self.studio_name:

            return False

        studios = self.load_all_studios()

        # -----------------------------------------------------
        # Check duplicate
        # -----------------------------------------------------

        for studio in studios:

            if (
                studio.get("title", "").lower()
                == new_name.lower()
                and studio.get("title")
                != self.studio_name
            ):

                self.status.setText(
                    "Status: A studio with this name already exists."
                )

                return False

        # -----------------------------------------------------
        # Rename current studio
        # -----------------------------------------------------

        for studio in studios:

            if studio.get("title") == self.studio_name:

                studio["title"] = new_name

                break

        config_path = self.get_config_path()

        try:

            with open(
                config_path,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    studios,
                    f,
                    indent=4,
                    ensure_ascii=False
                )

            self.studio_name = new_name

            self.title_label.setText(
                new_name
            )

            return True

        except Exception as e:

            print(
                f"❌ Could not rename studio: {e}"
            )

            return False
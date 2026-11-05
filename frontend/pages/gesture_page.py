from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QHBoxLayout,
    QFrame,
    QVBoxLayout,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QMessageBox,
)

from frontend.pages.studio_page import StudioPage
from frontend.components.gesture_recorder_dialog import GestureRecorderDialog
from frontend.styles.theme import (
    BG_DARK,
    SURFACE,
    SURFACE_HOVER,
    BORDER,
    PRIMARY,
    PRIMARY_HOVER,
    PRIMARY_PRESSED,
    PRIMARY_TEXT,
    SECONDARY_TEXT,
    TEXT_MUTED,
    ERROR,
)
from backend.profile_manager import ProfileManager
from backend.gestures.custom_gestures import CustomGestureStore
from backend.gestures.google_gesture_recognizer import BUILTIN_GESTURE_NAMES


class GesturePage(StudioPage):

    def __init__(self, parent=None):

        super().__init__(
            title="Gesture Studio",
            subtitle="Configure and manage your gesture controls.",
            parent=parent,
        )

        # -----------------------------------------
        # Profile
        # -----------------------------------------

        self.profile_manager = ProfileManager()
        self.profile_manager.load("presentation")

        self.gesture_map = (
            self.profile_manager.get_gesture_map()
        )

        # -----------------------------------------
        # Available actions
        # -----------------------------------------

        self.available_actions = [
            "ACTIVATE",
            "presentation_start",
            "presentation_end",
            "presentation_next",
            "presentation_previous",
        ]

        # -----------------------------------------
        # Supported gestures
        # -----------------------------------------

        self.builtin_gestures = list(BUILTIN_GESTURE_NAMES)

        # The user's own recorded gestures
        self.custom_store = CustomGestureStore()

        # -----------------------------------------
        # Store UI labels
        # -----------------------------------------

        self.action_labels = {}

        self.gesture_cards = {}

        # -----------------------------------------
        # Intro
        # -----------------------------------------

        intro = QLabel(
            "Assign gestures to actions and create your own controls."
        )

        intro.setStyleSheet(f"""
            color: {SECONDARY_TEXT};
            font-size: 14px;
        """)

        self.content_layout.addWidget(intro)

        # -----------------------------------------
        # Gesture list
        # -----------------------------------------

        self.gesture_list_layout = QVBoxLayout()

        self.gesture_list_layout.setSpacing(10)

        self.content_layout.addLayout(
            self.gesture_list_layout
        )

        # Build current gestures

        self.refresh_gesture_list()

        # -----------------------------------------
        # Add Gesture
        # -----------------------------------------

        add_button = QPushButton(
            "+ Add Gesture"
        )

        add_button.setCursor(
            Qt.PointingHandCursor
        )

        add_button.setStyleSheet(f"""
            QPushButton {{
                background: {PRIMARY};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 18px;
                font-size: 13px;
                font-weight: 600;
            }}

            QPushButton:hover {{
                background: {PRIMARY_HOVER};
            }}

            QPushButton:pressed {{
                background: {PRIMARY_PRESSED};
            }}
        """)

        add_button.clicked.connect(
            self.add_gesture
        )

        self.content_layout.addWidget(
            add_button,
            0,
            Qt.AlignLeft
        )

        # -----------------------------------------
        # Custom gestures
        # -----------------------------------------

        self._build_custom_section()

        self.content_layout.addStretch()

    # ==================================================
    # AVAILABLE GESTURES (built-in + custom)
    # ==================================================

    @property
    def available_gestures(self):

        return self.builtin_gestures + self.custom_store.names()

    # ==================================================
    # CUSTOM GESTURES SECTION
    # ==================================================

    def _build_custom_section(self):

        heading = QLabel("Your gestures")

        heading.setStyleSheet(f"""
            color: {PRIMARY_TEXT};
            font-size: 18px;
            font-weight: 700;
            margin-top: 12px;
            border: none;
            background: transparent;
        """)

        self.content_layout.addWidget(heading)

        info = QLabel(
            "Record any hand pose that's comfortable for you, "
            "then assign it to an action above."
        )

        info.setWordWrap(True)

        info.setStyleSheet(f"""
            color: {SECONDARY_TEXT};
            font-size: 14px;
            border: none;
            background: transparent;
        """)

        self.content_layout.addWidget(info)

        self.custom_list_layout = QVBoxLayout()

        self.custom_list_layout.setSpacing(10)

        self.content_layout.addLayout(
            self.custom_list_layout
        )

        record_button = QPushButton(
            "+ Record Custom Gesture"
        )

        record_button.setCursor(
            Qt.PointingHandCursor
        )

        record_button.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.04);
                color: {PRIMARY_TEXT};
                border: 1px solid {PRIMARY};
                border-radius: 10px;
                padding: 10px 18px;
                font-size: 14px;
                font-weight: 600;
            }}

            QPushButton:hover {{
                background: {SURFACE_HOVER};
            }}
        """)

        record_button.clicked.connect(
            self.record_custom_gesture
        )

        self.content_layout.addWidget(
            record_button,
            0,
            Qt.AlignLeft
        )

        self.refresh_custom_list()

    def refresh_custom_list(self):

        while self.custom_list_layout.count():

            widget = self.custom_list_layout.takeAt(0).widget()

            if widget:
                widget.deleteLater()

        self.custom_store.load()

        if not self.custom_store.gestures:

            empty = QLabel("No custom gestures yet.")

            empty.setStyleSheet(f"""
                color: {TEXT_MUTED};
                font-size: 13px;
                border: none;
                background: transparent;
        """)

            self.custom_list_layout.addWidget(empty)

            return

        for gesture in self.custom_store.gestures:

            self.create_custom_card(gesture)

    def create_custom_card(self, gesture):

        name = gesture["name"]

        card = QFrame()

        card.setStyleSheet(f"""
            QFrame {{
                background: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)

        layout = QHBoxLayout(card)

        layout.setContentsMargins(18, 14, 18, 14)

        name_label = QLabel(name)

        name_label.setStyleSheet(f"""
            color: {PRIMARY_TEXT};
            font-size: 15px;
            font-weight: 600;
            border: none;
            background: transparent;
        """)

        action = self.gesture_map.get(name)

        detail = (
            f"→  {action}"
            if action
            else "Not assigned yet"
        )

        detail_label = QLabel(detail)

        detail_label.setStyleSheet(f"""
            color: {SECONDARY_TEXT};
            font-size: 14px;
            border: none;
            background: transparent;
        """)

        delete_button = QPushButton("Delete")

        delete_button.setCursor(Qt.PointingHandCursor)

        delete_button.setAccessibleName(f"Delete gesture {name}")

        delete_button.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.04);
                color: {ERROR};
                border: none;
                border-radius: 8px;
                padding: 7px 14px;
            }}

            QPushButton:hover {{
                background: rgba(239, 68, 68, 0.12);
            }}
        """)

        delete_button.clicked.connect(
            lambda checked=False, n=name:
            self.delete_custom_gesture(n)
        )

        layout.addWidget(name_label)
        layout.addStretch()
        layout.addWidget(detail_label)
        layout.addStretch()
        layout.addWidget(delete_button)

        self.custom_list_layout.addWidget(card)

    def record_custom_gesture(self):

        dialog = GestureRecorderDialog(
            self.builtin_gestures,
            store=self.custom_store,
            parent=self,
        )

        if dialog.exec() and dialog.saved_name:

            self.refresh_custom_list()

            self.status_label.setText(
                f'Status: Saved "{dialog.saved_name}". '
                "Use + Add Gesture to assign it to an action."
            )

    def delete_custom_gesture(self, name):

        assigned = name in self.gesture_map

        message = f'Delete your "{name}" gesture?'

        if assigned:
            message += "\n\nIts action assignment will be removed too."

        answer = QMessageBox.question(
            self,
            "Delete Gesture",
            message,
        )

        if answer != QMessageBox.Yes:
            return

        self.custom_store.delete(name)

        if assigned:
            self.profile_manager.remove_gesture(name)
            self.refresh_gesture_list()

        self.refresh_custom_list()

    # ==================================================
    # REFRESH GESTURE LIST
    # ==================================================

    def refresh_gesture_list(self):

        # Remove old widgets

        while self.gesture_list_layout.count():

            item = (
                self.gesture_list_layout
                .takeAt(0)
            )

            widget = item.widget()

            if widget:
                widget.deleteLater()

        self.action_labels.clear()
        self.gesture_cards.clear()

        # Get latest data

        self.gesture_map = (
            self.profile_manager
            .get_gesture_map()
        )

        # Create cards

        for gesture, action in self.gesture_map.items():

            self.create_gesture_card(
                gesture,
                action
            )

        # Custom gesture cards show their assigned action, so keep them in sync.
        if hasattr(self, "custom_list_layout"):
            self.refresh_custom_list()

    # ==================================================
    # CREATE GESTURE CARD
    # ==================================================

    def create_gesture_card(
        self,
        gesture,
        action
    ):

        card = QFrame()

        card.setStyleSheet(f"""
            QFrame {{
                background: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)

        layout = QHBoxLayout(card)

        layout.setContentsMargins(
            18,
            14,
            18,
            14
        )

        # Gesture

        gesture_label = QLabel(
            gesture
        )

        gesture_label.setStyleSheet(f"""
            color: {PRIMARY_TEXT};
            font-size: 15px;
            font-weight: 600;
            border: none;
            background: transparent;
        """)

        # Action

        action_label = QLabel(
            "→  " + action
        )

        action_label.setStyleSheet(f"""
            color: {SECONDARY_TEXT};
            font-size: 14px;
            border: none;
            background: transparent;
        """)

        self.action_labels[
            gesture
        ] = action_label

        # Edit button

        edit_button = QPushButton(
            "Edit"
        )

        edit_button.setCursor(
            Qt.PointingHandCursor
        )

        edit_button.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.04);
                color: {PRIMARY_TEXT};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 7px 14px;
                font-size: 12px;
                font-weight: 500;
            }}

            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.16);
                color: #FFFFFF;
            }}
        """)

        edit_button.clicked.connect(
            lambda checked=False,
            g=gesture,
            a=action:
            self.edit_gesture(g, a)
        )

        # Layout

        layout.addWidget(
            gesture_label
        )

        layout.addStretch()

        layout.addWidget(
            action_label
        )

        layout.addStretch()

        layout.addWidget(
            edit_button
        )

        self.gesture_list_layout.addWidget(
            card
        )

        self.gesture_cards[
            gesture
        ] = card

    # ==================================================
    # EDIT GESTURE
    # ==================================================

    def edit_gesture(
        self,
        gesture,
        current_action
    ):

        dialog = QDialog(self)

        dialog.setWindowTitle(
            "Edit Gesture"
        )

        dialog.setFixedSize(
            400,
            220
        )

        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
            QLabel {{
                color: {PRIMARY_TEXT};
            }}
            QComboBox {{
                background-color: {BG_DARK};
                color: {PRIMARY_TEXT};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 8px 12px;
            }}
            QComboBox:focus {{
                border: 1px solid {PRIMARY};
            }}
            QDialogButtonBox QPushButton {{
                background-color: {PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 6px 16px;
                font-weight: 600;
            }}
            QDialogButtonBox QPushButton:hover {{
                background-color: {PRIMARY_HOVER};
            }}
        """)

        layout = QVBoxLayout(
            dialog
        )

        # Gesture

        gesture_label = QLabel(
            f"Gesture: {gesture}"
        )

        gesture_label.setStyleSheet(f"""
            color: {PRIMARY_TEXT};
            font-size: 15px;
            font-weight: 600;
        """)

        layout.addWidget(
            gesture_label
        )

        # Action

        action_label = QLabel(
            "Action:"
        )

        action_label.setStyleSheet(f"""
            color: {SECONDARY_TEXT};
            font-size: 13px;
        """)

        layout.addWidget(
            action_label
        )

        # Dropdown

        action_box = QComboBox()

        action_box.addItems(
            self.available_actions
        )

        index = action_box.findText(
            current_action
        )

        if index >= 0:

            action_box.setCurrentIndex(
                index
            )

        layout.addWidget(
            action_box
        )

        # Buttons

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save |
            QDialogButtonBox.Cancel
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

        # Save

        if dialog.exec():

            new_action = (
                action_box.currentText()
            )

            self.profile_manager.update_gesture(
                gesture,
                new_action
            )

            self.gesture_map = (
                self.profile_manager
                .get_gesture_map()
            )

            # Update label immediately

            if gesture in self.action_labels:

                self.action_labels[
                    gesture
                ].setText(
                    "→  " + new_action
                )

            self.refresh_custom_list()

    # ==================================================
    # ADD GESTURE
    # ==================================================

    def add_gesture(self):

        dialog = QDialog(self)

        dialog.setWindowTitle(
            "Add Gesture"
        )

        dialog.setFixedSize(
            400,
            240
        )

        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
            QLabel {{
                color: {PRIMARY_TEXT};
            }}
            QComboBox {{
                background-color: {BG_DARK};
                color: {PRIMARY_TEXT};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 8px 12px;
            }}
            QComboBox:focus {{
                border: 1px solid {PRIMARY};
            }}
            QDialogButtonBox QPushButton {{
                background-color: {PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 6px 16px;
                font-weight: 600;
            }}
            QDialogButtonBox QPushButton:hover {{
                background-color: {PRIMARY_HOVER};
            }}
        """)

        layout = QVBoxLayout(
            dialog
        )

        # Gesture

        gesture_label = QLabel(
            "Gesture:"
        )

        gesture_label.setStyleSheet(f"""
            color: {SECONDARY_TEXT};
            font-size: 13px;
        """)

        layout.addWidget(
            gesture_label
        )

        gesture_box = QComboBox()

        # Only show gestures
        # that aren't already used

        unused_gestures = [
            gesture
            for gesture in self.available_gestures
            if gesture not in self.gesture_map
        ]

        gesture_box.addItems(
            unused_gestures
        )

        layout.addWidget(
            gesture_box
        )

        # Action

        action_label = QLabel(
            "Action:"
        )

        action_label.setStyleSheet(f"""
            color: {SECONDARY_TEXT};
            font-size: 13px;
        """)

        layout.addWidget(
            action_label
        )

        action_box = QComboBox()

        action_box.addItems(
            self.available_actions
        )

        layout.addWidget(
            action_box
        )

        # Buttons

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save |
            QDialogButtonBox.Cancel
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

        # No gestures left

        if not unused_gestures:

            QMessageBox.information(
                self,
                "All Gestures Assigned",
                "Every available gesture already has an action.\n\n"
                "Use \"+ Record Custom Gesture\" below to teach "
                "LensFlow a new one."
            )

            return

        # Save

        if dialog.exec():

            gesture = (
                gesture_box.currentText()
            )

            action = (
                action_box.currentText()
            )

            # Safety check

            if gesture in self.gesture_map:

                QMessageBox.warning(
                    self,
                    "Gesture Already Exists",
                    f"{gesture} is already configured."
                )

                return

            # Save

            self.profile_manager.update_gesture(
                gesture,
                action
            )

            # Refresh everything

            self.refresh_gesture_list()
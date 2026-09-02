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
from backend.profile_manager import ProfileManager


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

        self.available_gestures = [
            "✋ Open Palm",
            "✊ Fist",
            "✌️ Peace",
            "👍 Thumbs Up",
            "👎 Thumbs Down",
        ]

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

        intro.setStyleSheet("""
            color: #9CA3AF;
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

        add_button.setStyleSheet("""
            QPushButton {
                background: #2563EB;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 18px;
                font-size: 14px;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #3B82F6;
            }
        """)

        add_button.clicked.connect(
            self.add_gesture
        )

        self.content_layout.addWidget(
            add_button,
            0,
            Qt.AlignLeft
        )

        self.content_layout.addStretch()

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

    # ==================================================
    # CREATE GESTURE CARD
    # ==================================================

    def create_gesture_card(
        self,
        gesture,
        action
    ):

        card = QFrame()

        card.setStyleSheet("""
            QFrame {
                background: #20202A;
                border-radius: 12px;
            }
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

        gesture_label.setStyleSheet("""
            color: white;
            font-size: 15px;
            font-weight: 600;
        """)

        # Action

        action_label = QLabel(
            "→  " + action
        )

        action_label.setStyleSheet("""
            color: #9CA3AF;
            font-size: 14px;
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

        edit_button.setStyleSheet("""
            QPushButton {
                background: #2A2A36;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 7px 14px;
            }

            QPushButton:hover {
                background: #363646;
            }
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

        layout = QVBoxLayout(
            dialog
        )

        # Gesture

        gesture_label = QLabel(
            f"Gesture: {gesture}"
        )

        gesture_label.setStyleSheet("""
            color: white;
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

        action_label.setStyleSheet("""
            color: #9CA3AF;
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

        layout = QVBoxLayout(
            dialog
        )

        # Gesture

        gesture_label = QLabel(
            "Gesture:"
        )

        gesture_label.setStyleSheet("""
            color: #9CA3AF;
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

        action_label.setStyleSheet("""
            color: #9CA3AF;
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
                "No Gestures Available",
                "All supported gestures are already configured."
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
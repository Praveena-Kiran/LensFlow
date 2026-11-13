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
from frontend.components.gesture_test_dialog import GestureTestDialog
from frontend.components.trigger_editor import ActionTriggerEditor
from frontend.components.motion_recorder_dialog import MotionRecorderDialog
from backend.gestures.motions import BUILTIN_MOTION_NAMES, FINGERTIP, MotionStore
from frontend.styles.theme import (
    ON_PRIMARY,
    OVERLAY_1,
    OVERLAY_2,
    OVERLAY_BORDER,
    TEXT_STRONG,
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
from backend.automation.events import friendly_action
from backend.gestures.custom_gestures import CustomGestureStore
from backend.gestures.google_gesture_recognizer import BUILTIN_GESTURE_NAMES
from backend.app_info import APP_NAME


class GesturePage(StudioPage):

    def __init__(self, parent=None):

        super().__init__(
            title="Gesture Studio",
            subtitle="Choose the gestures, motions and voice commands that control your presentations.",
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

        # The user's own recorded motions
        self.motion_store = MotionStore()

        # -----------------------------------------
        # Store UI labels
        # -----------------------------------------



        # -----------------------------------------
        # Intro
        # -----------------------------------------

        intro = QLabel(
            "Each action can use a hand gesture, a motion, a voice command, "
            "or several at once. To use them in your own studios, choose one "
            "for each event inside that studio."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet(f"""
            color: {SECONDARY_TEXT};
            font-size: 14px;
        """)

        self.content_layout.addWidget(intro)

        # -----------------------------------------
        # Actions and their triggers (gestures / motions)
        # -----------------------------------------

        self.trigger_editor = ActionTriggerEditor(
            self.profile_manager,
            ["presentation_start", "presentation_next",
             "presentation_previous", "presentation_end", "ACTIVATE"],
            custom_gestures=lambda: self.custom_store.names(),
            custom_motions=lambda: self.motion_store.names(),
        )
        self.trigger_editor.changed.connect(self._on_triggers_changed)

        self.content_layout.addWidget(self.trigger_editor)

        test_button = QPushButton(
            "Test Gestures && Motions"
        )

        test_button.setCursor(
            Qt.PointingHandCursor
        )

        test_button.setAccessibleName(
            "Test gestures with the camera"
        )

        test_button.setStyleSheet(f"""
            QPushButton {{
                background: {OVERLAY_1};
                color: {PRIMARY_TEXT};
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 10px 18px;
                font-size: 13px;
                font-weight: 600;
            }}

            QPushButton:hover {{
                background: {SURFACE_HOVER};
                border: 1px solid {PRIMARY};
            }}
        """)

        test_button.clicked.connect(
            self.test_gestures
        )

        button_row = QHBoxLayout()

        button_row.setSpacing(10)

        button_row.addWidget(test_button)

        button_row.addStretch()

        self.content_layout.addLayout(
            button_row
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

        return (
            self.builtin_gestures
            + list(BUILTIN_MOTION_NAMES)
            + self.custom_store.names()
            + self.motion_store.names()
        )

    # ==================================================
    # CUSTOM GESTURES SECTION
    # ==================================================

    # The two kinds of user-recorded triggers shown on this page.
    SECTIONS = {
        "gesture": {
            "title": "Your gestures",
            "info": "Record any hand pose that's comfortable for you, "
                    "then assign it to an action above.",
            "button": "+ Record Custom Gesture",
            "empty": "No custom gestures yet.",
            "noun": "gesture",
        },
        "motion": {
            "title": "Your motions",
            "info": "Swipe left, right, up and down are built in. Record "
                    "your own movements, like a wave or a circle.",
            "button": "+ Record Custom Motion",
            "empty": "No custom motions yet.",
            "noun": "motion",
        },
    }

    def _store(self, kind):
        return self.custom_store if kind == "gesture" else self.motion_store

    def _entries(self, kind):
        store = self._store(kind)
        return store.gestures if kind == "gesture" else store.motions

    def _build_custom_section(self):

        self.section_lists = {}

        for kind in ("gesture", "motion"):
            self._build_section(kind)

        self.refresh_custom_list()

    def _build_section(self, kind):

        config = self.SECTIONS[kind]

        heading = QLabel(config["title"])

        heading.setStyleSheet(f"""
            color: {PRIMARY_TEXT};
            font-size: 18px;
            font-weight: 700;
            margin-top: 12px;
            border: none;
            background: transparent;
        """)

        self.content_layout.addWidget(heading)

        info = QLabel(config["info"])

        info.setWordWrap(True)

        info.setStyleSheet(f"""
            color: {SECONDARY_TEXT};
            font-size: 14px;
            border: none;
            background: transparent;
        """)

        self.content_layout.addWidget(info)

        list_layout = QVBoxLayout()

        list_layout.setSpacing(10)

        self.content_layout.addLayout(list_layout)

        self.section_lists[kind] = list_layout

        if kind == "gesture":
            # Older code refers to this name.
            self.custom_list_layout = list_layout

        record_button = QPushButton(config["button"])

        record_button.setCursor(Qt.PointingHandCursor)

        record_button.setStyleSheet(f"""
            QPushButton {{
                background: {OVERLAY_1};
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
            if kind == "gesture"
            else self.record_custom_motion
        )

        self.content_layout.addWidget(record_button, 0, Qt.AlignLeft)

    def refresh_custom_list(self):

        for kind, list_layout in self.section_lists.items():

            while list_layout.count():

                widget = list_layout.takeAt(0).widget()

                if widget:
                    widget.deleteLater()

            self._store(kind).load()

            entries = self._entries(kind)

            if not entries:

                empty = QLabel(self.SECTIONS[kind]["empty"])

                empty.setStyleSheet(f"""
                    color: {TEXT_MUTED};
                    font-size: 13px;
                    border: none;
                    background: transparent;
                """)

                list_layout.addWidget(empty)

                continue

            for entry in entries:
                self.create_custom_card(entry, kind)

    def create_custom_card(self, entry, kind="gesture"):

        name = entry["name"]

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

        detail = f"→  {friendly_action(action)}" if action else "Not assigned yet"

        if kind == "motion":
            if entry.get("point") == FINGERTIP:
                detail += "   ·   follows your fingertip"
            else:
                detail += "   ·   follows your whole hand"

        detail_label = QLabel(detail)

        detail_label.setStyleSheet(f"""
            color: {SECONDARY_TEXT};
            font-size: 14px;
            border: none;
            background: transparent;
        """)

        delete_button = QPushButton("Delete")

        delete_button.setCursor(Qt.PointingHandCursor)

        delete_button.setAccessibleName(
            f"Delete {self.SECTIONS[kind]['noun']} {name}"
        )

        delete_button.setStyleSheet(f"""
            QPushButton {{
                background: {OVERLAY_1};
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
            lambda checked=False, n=name, k=kind:
            self.delete_custom(k, n)
        )

        layout.addWidget(name_label)
        layout.addStretch()
        layout.addWidget(detail_label)
        layout.addStretch()
        layout.addWidget(delete_button)

        self.section_lists[kind].addWidget(card)

    def test_gestures(self):

        dialog = GestureTestDialog(
            gesture_map=self.gesture_map,
            store=self.custom_store,
            parent=self,
        )

        dialog.exec()

    def _taken_names(self):
        """Names a new gesture or motion can't use."""
        return (
            self.builtin_gestures
            + list(BUILTIN_MOTION_NAMES)
            + self.custom_store.names()
            + self.motion_store.names()
        )

    def record_custom_gesture(self):

        taken = [
            n for n in self._taken_names()
            if n not in self.custom_store.names()  # re-recording is allowed
        ]

        dialog = GestureRecorderDialog(
            taken,
            store=self.custom_store,
            parent=self,
        )

        self._after_recording(dialog)

    def record_custom_motion(self):

        taken = [
            n for n in self._taken_names()
            if n not in self.motion_store.names()
        ]

        dialog = MotionRecorderDialog(
            taken_names=taken,
            store=self.motion_store,
            parent=self,
        )

        self._after_recording(dialog)

    def _after_recording(self, dialog):

        if dialog.exec() and dialog.saved_name:

            self.refresh_custom_list()

            self.status_label.setText(
                f'Status: Saved "{dialog.saved_name}". '
                "Use + Add Gesture to assign it to an action."
            )

    def delete_custom_gesture(self, name):
        self.delete_custom("gesture", name)

    def delete_custom(self, kind, name):

        noun = self.SECTIONS[kind]["noun"]

        assigned = name in self.gesture_map

        message = f'Delete your "{name}" {noun}?'

        if assigned:
            message += "\n\nIts action assignment will be removed too."

        answer = QMessageBox.question(
            self,
            f"Delete {noun.title()}",
            message,
        )

        if answer != QMessageBox.Yes:
            return

        self._store(kind).delete(name)

        if assigned:
            self.profile_manager.remove_gesture(name)
            self.refresh_gesture_list()

        self.refresh_custom_list()

    # ==================================================
    # ACTIONS AND TRIGGERS
    # ==================================================

    def refresh_gesture_list(self):

        self.gesture_map = self.profile_manager.get_gesture_map()

        self.trigger_editor.refresh()

        # Custom gesture/motion cards show their assigned action.
        if hasattr(self, "section_lists"):
            self.refresh_custom_list()

    def _on_triggers_changed(self):

        self.gesture_map = self.profile_manager.get_gesture_map()

        if hasattr(self, "section_lists"):
            self.refresh_custom_list()

"""
Wield - Presentation Studio

One row per action: pick the gesture (or motion) that runs it, and type
what to say after "Hey Wield". Start / End buttons at the bottom.

Changes save straight away. Gesture Studio offers more (several gestures
per action, recording your own); rows show "+N more" when an action has
extra triggers set up there.
"""

import os

from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from backend.automation.controllers.powerpoint_controller import PowerPointController
from backend.automation.events import friendly_action
from backend.automation.presentation_bindings import (
    ACTIONS,
    binding,
    check_voice,
    set_gesture,
    set_voice,
)
from backend.automation.triggers import catalogue
from backend.paths import APP_DIR
from backend.profile_manager import ProfileManager
from backend.settings import gesture_settings
from frontend.pages.studio_page import StudioPage
from frontend.styles.theme import (
    BG_DARK,
    BORDER,
    ERROR,
    ON_PRIMARY,
    OVERLAY_1,
    OVERLAY_2,
    PRIMARY,
    PRIMARY_HOVER,
    PRIMARY_MUTED,
    PRIMARY_TEXT,
    SECONDARY_TEXT,
    SUCCESS,
    SURFACE,
    SURFACE_HOVER,
    TEXT_MUTED,
)

NO_GESTURE = "No gesture"

ACTION_DESCRIPTIONS = {
    "presentation_start": "Starts the slideshow from the beginning",
    "presentation_next": "Moves forward one slide",
    "presentation_previous": "Goes back one slide",
    "presentation_end": "Closes the slideshow",
}


ACTION_ICONS = {
    "presentation_start": "\u25B6",
    "presentation_next": "\u2192",
    "presentation_previous": "\u2190",
    "presentation_end": "\u25A0",
}

CHEVRON = os.path.join(APP_DIR, "frontend", "styles", "icons", "chevron-down.svg").replace("\\", "/")


class _FocusGlow(QObject):
    """Lights up the voice pill while its text box has focus."""

    def __init__(self, pill):
        super().__init__(pill)
        self.pill = pill

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.Type.FocusIn, QEvent.Type.FocusOut):
            self.pill.setProperty("focused", event.type() == QEvent.Type.FocusIn)
            self.pill.style().unpolish(self.pill)
            self.pill.style().polish(self.pill)
        return False


def _recorded_names():
    """(your gestures, your motions), or empty lists if they can't load."""
    try:
        from backend.gestures.custom_gestures import CustomGestureStore
        gestures = CustomGestureStore().names()
    except Exception:
        gestures = []
    try:
        from backend.gestures.motions import MotionStore
        motions = MotionStore().names()
    except Exception:
        motions = []
    return gestures, motions


class _ActionRow:
    """Widgets for one action (kept together for refresh)."""

    def __init__(self, action):
        self.action = action

        self.gesture = QComboBox()
        self.gesture.setObjectName("GesturePill")
        self.gesture.setAccessibleName(f"Gesture for {friendly_action(action)}")
        self.gesture.setFixedWidth(230)
        self.gesture.setFixedHeight(38)
        self.gesture.setCursor(Qt.CursorShape.PointingHandCursor)

        # "🎤 Hey Wield, [what to say]" as one rounded field.
        self.pill = QFrame()
        self.pill.setObjectName("VoicePill")
        self.pill.setFixedHeight(38)
        pill_layout = QHBoxLayout(self.pill)
        pill_layout.setContentsMargins(14, 0, 10, 0)
        pill_layout.setSpacing(6)

        self.mic = QLabel("\U0001F3A4")
        self.mic.setObjectName("VoiceMic")
        self.wake = QLabel("Hey Wield,")
        self.wake.setObjectName("VoiceWake")

        self.phrase = QLineEdit()
        self.phrase.setObjectName("VoiceInput")
        self.phrase.setAccessibleName(f"Voice command for {friendly_action(action)}")
        self.phrase.setPlaceholderText("what to say")
        self.phrase.installEventFilter(_FocusGlow(self.pill))

        pill_layout.addWidget(self.mic)
        pill_layout.addWidget(self.wake)
        pill_layout.addWidget(self.phrase, 1)

        self.hint = QLabel()
        self.hint.setWordWrap(True)


class PresentationPage(StudioPage):

    # Gestures or phrases changed (the running camera/voice should reload).
    bindings_changed = Signal()

    # "More options" link.
    open_gesture_studio = Signal()

    # Turn the camera + microphone on (True) or off (False). MainWindow
    # does it and reports back with set_listening().
    listening_requested = Signal(bool)

    def __init__(self):
        super().__init__(
            "Presentation Studio",
            "Choose how you control your slides: a gesture, your voice, or both."
        )

        self.powerpoint = PowerPointController()
        self.profile = ProfileManager()
        self.rows = {}
        self.wake_labels = []
        self._loading = False

        self.setStyleSheet(self.styleSheet() + f"""
            QFrame#Card {{
                background-color: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 18px;
            }}
            QFrame#ActionTile {{
                background-color: {OVERLAY_1};
                border: 1px solid transparent;
                border-radius: 16px;
            }}
            QFrame#ActionTile:hover {{
                background-color: {SURFACE_HOVER};
                border: 1px solid {BORDER};
            }}
            QLabel#ActionBadge {{
                background-color: {PRIMARY_MUTED};
                color: {PRIMARY};
                border-radius: 18px;
                font-size: 14px;
                font-weight: 700;
            }}

            QComboBox#GesturePill {{
                background-color: {BG_DARK};
                color: {PRIMARY_TEXT};
                border: 1px solid {BORDER};
                border-radius: 19px;
                padding: 0 14px;
                font-size: 13px;
            }}
            QComboBox#GesturePill:hover {{ border: 1px solid {PRIMARY}; }}
            QComboBox#GesturePill:focus {{ border: 1px solid {PRIMARY}; }}
            QComboBox#GesturePill::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 26px;
                border: none;
                background: transparent;
            }}
            QComboBox#GesturePill::down-arrow {{
                image: url({CHEVRON});
                width: 12px;
                height: 12px;
            }}
            QComboBox#GesturePill QAbstractItemView {{
                background-color: {SURFACE};
                color: {PRIMARY_TEXT};
                border: 1px solid {BORDER};
                border-radius: 12px;
                padding: 6px;
                outline: 0;
                selection-background-color: {PRIMARY_MUTED};
                selection-color: {PRIMARY_TEXT};
            }}

            QFrame#VoicePill {{
                background-color: {BG_DARK};
                border: 1px solid {BORDER};
                border-radius: 19px;
            }}
            QFrame#VoicePill:hover {{ border: 1px solid {PRIMARY}; }}
            QFrame#VoicePill[focused="true"] {{
                border: 1px solid {PRIMARY};
                background-color: {SURFACE};
            }}
            QFrame#VoicePill[invalid="true"] {{ border: 1px solid {ERROR}; }}
            QLabel#VoiceMic {{ background: transparent; border: none; font-size: 13px; }}
            QLabel#VoiceWake {{
                background: transparent; border: none;
                color: {TEXT_MUTED}; font-size: 13px; font-weight: 600;
            }}
            QLineEdit#VoiceInput {{
                background: transparent;
                border: none;
                color: {PRIMARY_TEXT};
                font-size: 13px;
                padding: 0;
            }}
        """)

        self.listening = False

        self.content_layout.addWidget(self._build_controls())
        self.content_layout.addStretch(1)
        self.content_layout.addWidget(self._build_session())

        # The base page's "Status: Ready" footer duplicates the status card.
        self.status_label.hide()

        self.refresh_bindings()

    # ---------------------------------------------------------
    # Layout
    # ---------------------------------------------------------

    def _card(self):
        frame = QFrame()
        frame.setObjectName("Card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(6)
        return frame, layout

    def _label(self, text, color=PRIMARY_TEXT, size=13, weight=400):
        label = QLabel(text)
        label.setStyleSheet(
            f"color: {color}; font-size: {size}px; font-weight: {weight}; "
            "border: none; background: transparent;"
        )
        return label

    def _build_controls(self):
        frame, layout = self._card()
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(10)

        header = QVBoxLayout()
        header.setSpacing(2)
        header.addWidget(self._label("Your controls", PRIMARY_TEXT, 16, 700))
        header.addWidget(self._label(
            "Pick a gesture, a phrase, or both for each action.", TEXT_MUTED, 12
        ))
        layout.addLayout(header)

        self.voice_note = self._label("", TEXT_MUTED, 12)
        self.voice_note.setWordWrap(True)
        layout.addWidget(self.voice_note)

        for action in ACTIONS:
            row = _ActionRow(action)
            self.rows[action] = row
            self.wake_labels.append(row.wake)
            layout.addWidget(self._build_tile(row))

            row.gesture.currentIndexChanged.connect(
                lambda _i, a=action: self._on_gesture_chosen(a)
            )
            row.phrase.textChanged.connect(lambda _t, a=action: self._on_phrase_typed(a))
            row.phrase.editingFinished.connect(lambda a=action: self._on_phrase_done(a))

        more = QPushButton("More options in Gesture Studio  \u2192")
        more.setCursor(Qt.CursorShape.PointingHandCursor)
        more.setToolTip("Several gestures per action, record your own gestures and motions")
        more.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: none; color: {PRIMARY};
                font-size: 12px; font-weight: 600; text-align: left; padding: 4px 2px;
            }}
            QPushButton:hover {{ color: {PRIMARY_HOVER}; }}
        """)
        more.clicked.connect(self.open_gesture_studio.emit)
        layout.addWidget(more, 0, Qt.AlignmentFlag.AlignLeft)
        return frame

    def _build_tile(self, row):
        tile = QFrame()
        tile.setObjectName("ActionTile")
        tile.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        outer = QVBoxLayout(tile)
        outer.setContentsMargins(14, 10, 14, 10)
        outer.setSpacing(4)

        line = QHBoxLayout()
        line.setSpacing(14)

        badge = QLabel(ACTION_ICONS[row.action])
        badge.setObjectName("ActionBadge")
        badge.setFixedSize(36, 36)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        line.addWidget(badge)

        names = QVBoxLayout()
        names.setSpacing(1)
        names.addWidget(self._label(friendly_action(row.action), PRIMARY_TEXT, 14, 600))
        names.addWidget(self._label(ACTION_DESCRIPTIONS[row.action], TEXT_MUTED, 12))
        name_box = QFrame()
        name_box.setStyleSheet("background: transparent; border: none;")
        name_box.setLayout(names)
        # Same width on every row so the controls line up.
        name_box.setFixedWidth(250)
        line.addWidget(name_box)

        line.addWidget(row.gesture)
        line.addWidget(row.pill, 1)
        outer.addLayout(line)

        # Hints line up under the controls, not under the badge.
        hint_line = QHBoxLayout()
        hint_line.setContentsMargins(36 + 14 + 250 + 14, 0, 0, 0)
        hint_line.addWidget(row.hint)
        outer.addLayout(hint_line)
        return tile

    def _button(self, text, primary=False, danger=False):
        button = QPushButton(text)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        if primary:
            style = f"background: {PRIMARY}; color: {ON_PRIMARY}; border: none;"
            hover = f"background: {PRIMARY_HOVER};"
        elif danger:
            style = f"background: {OVERLAY_1}; color: {ERROR}; border: 1px solid {BORDER};"
            hover = f"background: {OVERLAY_2};"
        else:
            style = f"background: {OVERLAY_1}; color: {PRIMARY_TEXT}; border: 1px solid {BORDER};"
            hover = f"background: {OVERLAY_2};"
        button.setStyleSheet(f"""
            QPushButton {{ {style} border-radius: 17px; padding: 9px 22px;
                           font-size: 14px; font-weight: 600; }}
            QPushButton:hover {{ {hover} }}
        """)
        return button

    def _build_session(self):
        """Bottom bar: camera state, status, and the presentation buttons."""
        frame, layout = self._card()
        layout.setSpacing(12)

        top = QHBoxLayout()
        top.setSpacing(12)

        self.camera_pill = QLabel()
        top.addWidget(self.camera_pill)

        self.status = self._label("", SECONDARY_TEXT, 13)
        self.status.setWordWrap(True)
        top.addWidget(self.status, 1)

        self.camera_button = self._button("Turn on camera")
        self.camera_button.setToolTip(
            "Use gestures and voice without starting the slideshow, e.g. "
            "when it's already running or to try your gestures."
        )
        self.camera_button.clicked.connect(
            lambda: self.listening_requested.emit(not self.listening)
        )
        top.addWidget(self.camera_button)
        layout.addLayout(top)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)

        self.start_button = self._button("\u25B6  Start presentation", primary=True)
        self.end_button = self._button("\u25A0  End presentation", danger=True)
        self.previous_button = self._button("\u2190  Previous")
        self.next_button = self._button("Next  \u2192")

        self.start_button.clicked.connect(self._start_presentation)
        self.end_button.clicked.connect(self._end_presentation)
        self.previous_button.clicked.connect(self._previous_slide)
        self.next_button.clicked.connect(self._next_slide)

        buttons.addWidget(self.start_button)
        buttons.addWidget(self.end_button)
        buttons.addStretch()
        buttons.addWidget(self.previous_button)
        buttons.addWidget(self.next_button)
        layout.addLayout(buttons)

        self.set_listening(False)
        return frame

    def set_listening(self, state):
        """
        Show whether the camera (and microphone) are on.
        state: False (off), "starting", or True (on).
        """
        self.listening = state is not False
        voice = gesture_settings.load()["voice_enabled"]
        devices = "Camera & mic" if voice else "Camera"

        if state is True:
            text, color = f"\u25CF  {devices} on", ERROR
            hint = "Listening for your gestures" + (" and voice." if voice else ".")
        elif state == "starting":
            text, color = "\u25CF  Starting camera\u2026", SECONDARY_TEXT
            hint = ""
        else:
            text, color = f"\u25CB  {devices} off", TEXT_MUTED
            hint = (f"Your {devices.lower()} only turn on when you start the "
                    "presentation." if voice else
                    "Your camera only turns on when you start the presentation.")

        self.camera_pill.setText(text)
        self.camera_pill.setStyleSheet(f"""
            color: {color}; font-size: 13px; font-weight: 700;
            background: {OVERLAY_1}; border: 1px solid {BORDER};
            border-radius: 15px; padding: 5px 14px;
        """)
        self.camera_button.setText("Turn off camera" if self.listening else "Turn on camera")
        self._set_status(hint, SECONDARY_TEXT, dot=False)

    # ---------------------------------------------------------
    # Data
    # ---------------------------------------------------------

    def refresh_bindings(self):
        """Re-read the saved gestures and phrases into the rows."""
        self._loading = True
        try:
            self.profile.load("presentation")
            gesture_map = self.profile.get_gesture_map()
            custom_gestures, custom_motions = _recorded_names()
            groups = [
                (title, names)
                for title, names in catalogue(custom_gestures, custom_motions)
                if title != "Voice commands"
            ]

            for action, row in self.rows.items():
                b = binding(gesture_map, action)
                self._fill_gestures(row, gesture_map, groups, b["gesture"])
                row.phrase.setText(b["phrase"])
                row.phrase.setProperty("invalid", False)
                row.pill.setProperty("invalid", False)
                self._restyle(row.pill)
                self._show_extras(row, b)

            settings = gesture_settings.load()
            wake = "Hey Wield," if settings["voice_wake_word"] else "Say"
            for label in self.wake_labels:
                label.setText(wake)
            self.voice_note.setText(
                "" if settings["voice_enabled"] else
                "Voice commands are off. Turn them on in Settings → Voice commands."
            )
            self.voice_note.setVisible(not settings["voice_enabled"])
        finally:
            self._loading = False

    def _fill_gestures(self, row, gesture_map, groups, current):
        combo = row.gesture
        combo.blockSignals(True)
        model = QStandardItemModel(combo)
        combo.setModel(model)
        combo.addItem(NO_GESTURE, None)

        for title, names in groups:
            combo.addItem(title.upper())
            model.item(model.rowCount() - 1).setEnabled(False)
            for name in names:
                used = gesture_map.get(name)
                label = f"   {name}"
                if used and used != row.action:
                    label += f"   (now: {friendly_action(used)})"
                combo.addItem(label, name)

        index = combo.findData(current) if current else 0
        if current and index < 0:
            # A trigger that's no longer offered (e.g. a deleted recording).
            combo.addItem(f"{current}  (missing)", current)
            index = combo.count() - 1
        combo.setCurrentIndex(max(index, 0))
        combo.blockSignals(False)

    def _show_extras(self, row, b, note=""):
        parts = []
        if note:
            parts.append(note)
        extras = []
        if b["more_gestures"]:
            n = b["more_gestures"]
            extras.append(f"{n} more gesture" + ("s" if n > 1 else ""))
        if b["more_phrases"]:
            n = b["more_phrases"]
            extras.append(f"{n} more phrase" + ("s" if n > 1 else ""))
        if extras:
            parts.append("+ " + " and ".join(extras) + " in Gesture Studio")
        self._hint(row, "   ".join(parts), TEXT_MUTED)

    def _hint(self, row, text, color):
        row.hint.setText(text)
        row.hint.setVisible(bool(text))
        row.hint.setStyleSheet(
            f"color: {color}; font-size: 11px; border: none; background: transparent;"
        )

    @staticmethod
    def _restyle(widget):
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def _save(self):
        self.profile.save_profile()
        self.bindings_changed.emit()

    # ---------------------------------------------------------
    # Editing
    # ---------------------------------------------------------

    def _on_gesture_chosen(self, action):
        if self._loading:
            return
        row = self.rows[action]
        gesture = row.gesture.currentData()
        note = set_gesture(self.profile.get_gesture_map(), action, gesture)
        self._save()
        # Another row may have lost its gesture, so redraw them all.
        self.refresh_bindings()
        self._show_extras(
            self.rows[action],
            binding(self.profile.get_gesture_map(), action),
            note,
        )

    def _on_phrase_typed(self, action):
        if self._loading:
            return
        row = self.rows[action]
        ok, message = check_voice(self.profile.get_gesture_map(), action, row.phrase.text())
        row.phrase.setProperty("invalid", not ok)
        row.pill.setProperty("invalid", not ok)
        self._restyle(row.pill)
        if ok:
            self._show_extras(row, binding(self.profile.get_gesture_map(), action))
        else:
            self._hint(row, message, ERROR)

    def _on_phrase_done(self, action):
        if self._loading:
            return
        row = self.rows[action]
        gesture_map = self.profile.get_gesture_map()
        before = binding(gesture_map, action)["phrase"]

        ok, message = set_voice(gesture_map, action, row.phrase.text())
        if not ok:
            self._hint(row, message, ERROR)
            return

        after = binding(gesture_map, action)["phrase"]
        if after != row.phrase.text():
            # Show it the way it's matched: "Onwards, please!" -> "onwards please".
            self._loading = True
            row.phrase.setText(after)
            self._loading = False

        if after == before:
            return

        self._save()
        self._show_extras(
            row,
            binding(gesture_map, action),
            "Saved." if after else "No voice command for this action.",
        )

    # ---------------------------------------------------------
    # Status + PowerPoint buttons
    # ---------------------------------------------------------

    def _set_status(self, text, color=SUCCESS, dot=True):
        self.status.setText(f"●  {text}" if dot and text else text)
        self.status.setStyleSheet(
            f"color: {color}; font-size: 13px; font-weight: 500; "
            "border: none; background: transparent;"
        )

    def _start_presentation(self):
        self.powerpoint.start_presentation()
        self._set_status("Presentation running", SUCCESS)
        # Gestures and voice come on with the slideshow, not before.
        if not self.listening:
            self.listening_requested.emit(True)

    def _next_slide(self):
        self.powerpoint.next_slide()
        self._set_status("Presentation running", SUCCESS)

    def _previous_slide(self):
        self.powerpoint.previous_slide()
        self._set_status("Presentation running", SUCCESS)

    def _end_presentation(self):
        self.powerpoint.end_presentation()
        if self.listening:
            self.listening_requested.emit(False)
        self._set_status("Presentation ended", SECONDARY_TEXT)

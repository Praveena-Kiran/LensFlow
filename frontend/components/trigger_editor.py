"""
Wield - Action trigger editor

One row per action (Start slideshow, Next slide, ...). Each row lists the
triggers that run it — hand gestures, motions, or a mix — as chips with a
remove button, plus "+ Add" to pick another. Picking a trigger that another
action uses moves it here (a trigger can only do one thing).
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import (
    QComboBox,
    QLineEdit,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from backend.automation.events import friendly_action
from backend.automation.triggers import (
    KIND_LABELS,
    MISSING,
    VOICE,
    catalogue,
    is_motion,
    trigger_kind,
    triggers_by_action,
)
from backend.voice.commands import check_phrase, is_voice_trigger, phrase_of, voice_trigger
from frontend.styles.theme import (
    BG_DARK,
    BORDER,
    ERROR,
    ON_PRIMARY,
    OVERLAY_1,
    OVERLAY_2,
    PRIMARY,
    PRIMARY_HOVER,
    PRIMARY_TEXT,
    SECONDARY_TEXT,
    SURFACE,
    TEXT_MUTED,
)

# Picker entry that lets the user type their own voice phrase.
CUSTOM_PHRASE = "__custom_voice_phrase__"

ACTION_HINTS = {
    "ACTIVATE": "Only used when “Require activation gesture” is on in Settings.",
}


class TriggerChip(QFrame):

    remove_requested = Signal(str)

    def __init__(self, trigger, kind, parent=None):
        super().__init__(parent)
        self.trigger = trigger
        self.setObjectName("TriggerChip")

        missing = kind == MISSING
        accent = ERROR if missing else (
            PRIMARY if is_motion(kind) or kind == VOICE else BORDER
        )

        self.setStyleSheet(f"""
            QFrame#TriggerChip {{
                background: {OVERLAY_1};
                border: 1px solid {accent};
                border-radius: 14px;
            }}
            QLabel {{ background: transparent; border: none; }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 6, 4)
        layout.setSpacing(6)

        name = QLabel(trigger)
        name.setStyleSheet(f"color: {PRIMARY_TEXT}; font-size: 13px; font-weight: 600;")
        layout.addWidget(name)

        tag = QLabel(KIND_LABELS[kind].lower())
        tag.setStyleSheet(
            f"color: {ERROR if missing else TEXT_MUTED}; font-size: 11px;"
        )
        if missing:
            tag.setToolTip("This recording was deleted, so it can't trigger anything.")
        layout.addWidget(tag)

        remove = QPushButton("✕")
        remove.setCursor(Qt.CursorShape.PointingHandCursor)
        remove.setFixedSize(22, 22)
        remove.setToolTip(f"Remove {trigger}")
        remove.setAccessibleName(f"Remove {trigger}")
        remove.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {SECONDARY_TEXT};
                border: none; border-radius: 11px; font-size: 11px;
            }}
            QPushButton:hover {{ background: {OVERLAY_2}; color: {PRIMARY_TEXT}; }}
        """)
        remove.clicked.connect(lambda: self.remove_requested.emit(self.trigger))
        layout.addWidget(remove)


class TriggerPickerDialog(QDialog):
    """Pick a gesture or motion for one action."""

    def __init__(self, action, gesture_map, custom_gestures, custom_motions, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Add a trigger: {friendly_action(action)}")
        self.setMinimumWidth(420)
        self.setStyleSheet(f"""
            QDialog {{ background-color: {SURFACE}; }}
            QLabel {{ color: {PRIMARY_TEXT}; }}
            QComboBox {{
                background-color: {BG_DARK}; color: {PRIMARY_TEXT};
                border: 1px solid {BORDER}; border-radius: 8px; padding: 8px 12px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {BG_DARK}; color: {PRIMARY_TEXT};
            }}
            QDialogButtonBox QPushButton {{
                background-color: {PRIMARY}; color: {ON_PRIMARY}; border: none;
                border-radius: 8px; padding: 6px 16px; font-weight: 600;
            }}
            QDialogButtonBox QPushButton:hover {{ background-color: {PRIMARY_HOVER}; }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        intro = QLabel(
            f"Choose a hand gesture, a motion or a voice command for "
            f"<b>{friendly_action(action)}</b>."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.box = QComboBox()
        model = QStandardItemModel(self.box)
        self.box.setModel(model)

        in_use_voice = [t for t in gesture_map if is_voice_trigger(t)]
        for title, names in catalogue(custom_gestures, custom_motions, in_use_voice):
            choices = [n for n in names if gesture_map.get(n) != action]
            if not choices:
                continue
            # Group heading (not selectable).
            self.box.addItem(title.upper())
            heading = model.item(model.rowCount() - 1)
            heading.setEnabled(False)
            for name in choices:
                current = gesture_map.get(name)
                label = f"   {name}"
                if current:
                    label += f"   (now: {friendly_action(current)})"
                self.box.addItem(label, name)
            if title == "Voice commands":
                self.box.addItem("   Type your own phrase\u2026", CUSTOM_PHRASE)

        layout.addWidget(self.box)

        self.phrase_input = QLineEdit()
        self.phrase_input.setPlaceholderText("What to say, e.g. \u201cnext one please\u201d")
        self.phrase_input.setAccessibleName("Voice phrase")
        self.phrase_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {BG_DARK}; color: {PRIMARY_TEXT};
                border: 1px solid {BORDER}; border-radius: 8px; padding: 8px 12px;
            }}
        """)
        self.phrase_input.textChanged.connect(self._update_note)
        self.phrase_input.hide()
        layout.addWidget(self.phrase_input)

        self.note = QLabel()
        self.note.setWordWrap(True)
        self.note.setStyleSheet(f"color: {SECONDARY_TEXT}; font-size: 12px;")
        layout.addWidget(self.note)

        self.gesture_map = gesture_map
        self.box.currentIndexChanged.connect(self._update_note)
        self._select_first_choice()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self._update_note()

    def _select_first_choice(self):
        for i in range(self.box.count()):
            if self.box.itemData(i):
                self.box.setCurrentIndex(i)
                return

    def selected(self):
        data = self.box.currentData()
        if data == CUSTOM_PHRASE:
            ok, _ = self._check_custom_phrase()
            return voice_trigger(self.phrase_input.text()) if ok else None
        return data

    def _check_custom_phrase(self):
        existing = [phrase_of(t) for t in self.gesture_map if is_voice_trigger(t)]
        return check_phrase(self.phrase_input.text(), existing)

    def _update_note(self, *_):
        custom = self.box.currentData() == CUSTOM_PHRASE
        self.phrase_input.setVisible(custom)

        name = self.selected()
        if hasattr(self, "ok_button"):
            self.ok_button.setEnabled(bool(name))

        if custom:
            ok, message = self._check_custom_phrase()
            self.note.setText(
                "Say \u201cHey Wield\u201d, then your phrase." if ok
                else (message if self.phrase_input.text() else "")
            )
            return

        current = self.gesture_map.get(name) if name else None
        note = (
            f"{name} is used for {friendly_action(current)} now. "
            "It will move to this action instead."
            if current else ""
        )
        if name and is_voice_trigger(name) and not note:
            note = "Say \u201cHey Wield\u201d, then this phrase. Turn on voice commands in Settings."
        self.note.setText(note)


class ActionTriggerEditor(QWidget):
    """Rows of actions, each with its gesture/motion triggers."""

    changed = Signal()

    def __init__(self, profile_manager, actions, custom_gestures, custom_motions, parent=None):
        """
        `custom_gestures` / `custom_motions` are callables returning the
        names of the user's recordings (they change while the page is open).
        """
        super().__init__(parent)
        self.profile_manager = profile_manager
        self.actions = list(actions)
        self.custom_gestures = custom_gestures
        self.custom_motions = custom_motions
        self.rows = {}

        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.setSpacing(10)
        self.refresh()

    # ---------------------------------------------------------
    # Build
    # ---------------------------------------------------------

    def refresh(self):
        while self.layout_.count():
            widget = self.layout_.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        self.rows.clear()

        gesture_map = self.profile_manager.get_gesture_map()
        grouped = triggers_by_action(gesture_map, self.actions)
        gestures, motions = self.custom_gestures(), self.custom_motions()

        for action in self.actions:
            row = self._build_row(action, grouped[action], gestures, motions)
            self.rows[action] = row
            self.layout_.addWidget(row)

    def _build_row(self, action, triggers, gestures, motions):
        row = QFrame()
        row.setObjectName("ActionRow")
        row.setStyleSheet(f"""
            QFrame#ActionRow {{
                background: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
            QLabel {{ background: transparent; border: none; }}
        """)

        layout = QVBoxLayout(row)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel(friendly_action(action))
        title.setStyleSheet(f"color: {PRIMARY_TEXT}; font-size: 15px; font-weight: 600;")
        header.addWidget(title)
        header.addStretch()

        add = QPushButton("+ Add gesture, motion or voice")
        add.setCursor(Qt.CursorShape.PointingHandCursor)
        add.setAccessibleName(f"Add a gesture, motion or voice command for {friendly_action(action)}")
        add.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {PRIMARY}; border: none;
                font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ color: {PRIMARY_HOVER}; }}
        """)
        add.clicked.connect(lambda checked=False, a=action: self.add_trigger(a))
        header.addWidget(add)
        layout.addLayout(header)

        hint = ACTION_HINTS.get(action)
        if hint:
            hint_label = QLabel(hint)
            hint_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
            layout.addWidget(hint_label)

        chips = QHBoxLayout()
        chips.setSpacing(8)
        if triggers:
            for trigger in triggers:
                chip = TriggerChip(trigger, trigger_kind(trigger, gestures, motions))
                chip.remove_requested.connect(self.remove_trigger)
                chips.addWidget(chip)
            if len(triggers) > 1:
                either = QLabel("any of these works")
                either.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
                chips.addWidget(either)
        else:
            empty = QLabel("Nothing assigned: this action won't run.")
            empty.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
            chips.addWidget(empty)
        chips.addStretch()
        layout.addLayout(chips)

        row.triggers = list(triggers)
        return row

    # ---------------------------------------------------------
    # Edit
    # ---------------------------------------------------------

    def add_trigger(self, action):
        dialog = TriggerPickerDialog(
            action,
            dict(self.profile_manager.get_gesture_map()),
            self.custom_gestures(),
            self.custom_motions(),
            self,
        )
        if dialog.exec() and dialog.selected():
            self.assign(dialog.selected(), action)

    def assign(self, trigger, action):
        """Make `trigger` run `action` (moving it from any other action)."""
        self.profile_manager.update_gesture(trigger, action)
        self.refresh()
        self.changed.emit()

    def remove_trigger(self, trigger):
        self.profile_manager.remove_gesture(trigger)
        self.refresh()
        self.changed.emit()

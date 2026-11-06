"""
History page: the user's routines (pause / delete), whether LensFlow keeps
running in the background so routines can fire, and their recent activity
(with a button to clear it). Everything shown here is stored locally.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from frontend.pages.studio_page import StudioPage
from frontend.styles.theme import (
    OVERLAY_1,
    BORDER,
    ERROR,
    PRIMARY,
    PRIMARY_TEXT,
    SECONDARY_TEXT,
    SURFACE,
    TEXT_MUTED,
)
from backend import startup
from backend.routines import ActivityLog, RoutineStore, describe_days
from backend.settings.settings_manager import SettingsManager


RECENT_LIMIT = 15

KIND_VERBS = {
    "studio": "Opened",
    "launch": "Launched",
    "event": "Ran",
}

TRIGGER_NOTES = {
    "gesture": "by gesture",
    "routine": "by routine",
    "click": "",
}


def routine_text(routine):
    verb = {"studio": "Open", "launch": "Launch"}.get(routine["kind"], "Run")
    target = routine["target"] if routine["kind"] != "event" else f'"{routine["target"]}"'
    return f"{verb} {target} at {routine['time']} {describe_days(routine['days'])}"


class ActivityPage(StudioPage):

    routines_changed = Signal()

    def __init__(self, parent=None):

        super().__init__(
            title="History",
            subtitle="Your routines and what LensFlow has done. Stored only on this computer.",
            parent=parent,
        )

        self.store = RoutineStore()
        self.log = ActivityLog()

        self.setStyleSheet(self.styleSheet() + f"""
            QCheckBox {{ color: {PRIMARY_TEXT}; font-size: 14px; spacing: 10px; background: transparent; }}
            QCheckBox::indicator {{
                width: 18px; height: 18px; border-radius: 5px;
                border: 1px solid {BORDER}; background: {SURFACE};
            }}
            QCheckBox::indicator:checked {{ background: {PRIMARY}; border: 1px solid {PRIMARY}; }}
        """)

        self._heading("Routines")

        self.routines_layout = QVBoxLayout()
        self.routines_layout.setSpacing(8)
        self.content_layout.addLayout(self.routines_layout)

        self._heading("Running in the background")

        settings = SettingsManager()

        self.background = QCheckBox("Keep LensFlow running in the system tray when I close it")
        self.background.setChecked(bool(settings.get_setting("run_in_background")))
        self.background.toggled.connect(
            lambda on: SettingsManager().set_setting("run_in_background", bool(on))
        )
        self.content_layout.addWidget(self.background)

        self.at_login = QCheckBox("Start LensFlow when I sign in to Windows")
        self.at_login.setChecked(startup.is_enabled())
        self.at_login.setEnabled(startup.is_supported())
        self.at_login.toggled.connect(self._on_at_login)
        self.content_layout.addWidget(self.at_login)

        note = QLabel("Routines only run while LensFlow is open, so keep one of these on.")
        note.setWordWrap(True)
        note.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; background: transparent;")
        self.content_layout.addWidget(note)

        header = QHBoxLayout()
        header.addWidget(self._heading("Recent activity", add=False))
        header.addStretch()

        clear = QPushButton("Clear history")
        clear.setCursor(Qt.PointingHandCursor)
        clear.setStyleSheet(self._button_style(ERROR))
        clear.clicked.connect(self._clear_history)
        header.addWidget(clear)

        self.content_layout.addLayout(header)

        self.recent_layout = QVBoxLayout()
        self.recent_layout.setSpacing(0)
        self.content_layout.addLayout(self.recent_layout)

        self.content_layout.addStretch()

        self.refresh()

    # -----------------------------------------------------

    def _heading(self, text, add=True):
        label = QLabel(text)
        label.setStyleSheet(f"""
            color: {PRIMARY_TEXT}; font-size: 17px; font-weight: 700;
            margin-top: 8px; border: none; background: transparent;
        """)
        if add:
            self.content_layout.addWidget(label)
        return label

    @staticmethod
    def _button_style(color=PRIMARY_TEXT):
        return f"""
            QPushButton {{
                background: {OVERLAY_1}; color: {color};
                border: 1px solid {BORDER}; border-radius: 8px;
                padding: 7px 14px; font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ border: 1px solid {PRIMARY}; }}
        """

    @staticmethod
    def _clear(layout):
        while layout.count():
            widget = layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()

    def _muted_label(self, text):
        label = QLabel(text)
        label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px; background: transparent;")
        return label

    # -----------------------------------------------------

    def refresh(self):

        self.store.load()

        # These can change elsewhere (e.g. accepting a routine turns on
        # running in the background), so re-read them.
        for box, value in (
            (self.background, bool(SettingsManager().get_setting("run_in_background"))),
            (self.at_login, startup.is_enabled()),
        ):
            box.blockSignals(True)
            box.setChecked(value)
            box.blockSignals(False)

        self._clear(self.routines_layout)

        if not self.store.routines:
            self.routines_layout.addWidget(self._muted_label(
                "No routines yet. When you do the same thing around the same "
                "time on most days, LensFlow will offer to do it for you."
            ))

        for routine in self.store.routines:
            self.routines_layout.addWidget(self._routine_row(routine))

        self._clear(self.recent_layout)

        entries = sorted(self.log.entries(), key=lambda e: e["_at"], reverse=True)[:RECENT_LIMIT]

        if not entries:
            self.recent_layout.addWidget(self._muted_label("Nothing yet."))

        for entry in entries:
            self.recent_layout.addWidget(self._activity_row(entry))

    def _routine_row(self, routine):

        row = QFrame()
        row.setStyleSheet(f"""
            QFrame {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 12px; }}
            QLabel {{ border: none; background: transparent; }}
        """)

        layout = QHBoxLayout(row)
        layout.setContentsMargins(16, 12, 12, 12)

        enabled = routine.get("enabled", True)

        text = QLabel(routine_text(routine))
        text.setStyleSheet(
            f"color: {PRIMARY_TEXT if enabled else TEXT_MUTED}; font-size: 14px;"
        )
        layout.addWidget(text, 1)

        toggle = QPushButton("Pause" if enabled else "Resume")
        toggle.setCursor(Qt.PointingHandCursor)
        toggle.setStyleSheet(self._button_style())
        toggle.setAccessibleName(f"{'Pause' if enabled else 'Resume'} routine: {routine_text(routine)}")
        toggle.clicked.connect(
            lambda checked=False, r=routine: self._set_enabled(r["id"], not r.get("enabled", True))
        )
        layout.addWidget(toggle)

        delete = QPushButton("Delete")
        delete.setCursor(Qt.PointingHandCursor)
        delete.setStyleSheet(self._button_style(ERROR))
        delete.setAccessibleName(f"Delete routine: {routine_text(routine)}")
        delete.clicked.connect(lambda checked=False, r=routine: self._delete(r))
        layout.addWidget(delete)

        return row

    def _activity_row(self, entry):

        row = QFrame()
        row.setStyleSheet(f"""
            QFrame {{ background: transparent; border: none; border-top: 1px solid {BORDER}; }}
            QLabel {{ border: none; background: transparent; }}
        """)

        layout = QHBoxLayout(row)
        layout.setContentsMargins(4, 10, 4, 10)

        when = QLabel(entry["_at"].strftime("%a %d %b, %H:%M"))
        when.setFixedWidth(130)
        when.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px;")
        layout.addWidget(when)

        verb = KIND_VERBS.get(entry.get("kind"), "Did")
        target = entry.get("target", "")
        if entry.get("kind") == "event" and entry.get("studio"):
            target = f'"{target}" in {entry["studio"]}'

        what = QLabel(f"{verb} {target}")
        what.setStyleSheet(f"color: {PRIMARY_TEXT}; font-size: 13px;")
        layout.addWidget(what, 1)

        note = TRIGGER_NOTES.get(entry.get("trigger"), "")
        if note:
            how = QLabel(note)
            how.setStyleSheet(f"color: {SECONDARY_TEXT}; font-size: 12px;")
            layout.addWidget(how)

        return row

    # -----------------------------------------------------

    def _set_enabled(self, routine_id, enabled):
        self.store.set_enabled(routine_id, enabled)
        self.refresh()
        self.routines_changed.emit()

    def _delete(self, routine):
        answer = QMessageBox.question(
            self, "Delete Routine", f"Stop doing this automatically?\n\n{routine_text(routine)}"
        )
        if answer == QMessageBox.Yes:
            self.store.remove(routine["id"])
            self.refresh()
            self.routines_changed.emit()

    def _clear_history(self):
        answer = QMessageBox.question(
            self,
            "Clear History",
            "Delete everything LensFlow has recorded about what you open and "
            "when? Your routines are kept.",
        )
        if answer == QMessageBox.Yes:
            self.log.clear()
            self.refresh()

    def _on_at_login(self, enabled):
        try:
            startup.set_enabled(enabled)
        except Exception as e:
            QMessageBox.warning(self, "Couldn't change startup", str(e))
            self.at_login.blockSignals(True)
            self.at_login.setChecked(startup.is_enabled())
            self.at_login.blockSignals(False)

    def showEvent(self, event):
        self.refresh()
        super().showEvent(event)

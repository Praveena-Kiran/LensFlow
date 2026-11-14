"""
Notifications: routine suggestions waiting for an answer, the automations
the user has turned on, and the options that let routines run on time.
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
    BORDER,
    ERROR,
    ON_PRIMARY,
    OVERLAY_1,
    PRIMARY,
    PRIMARY_HOVER,
    PRIMARY_TEXT,
    SURFACE,
    TEXT_MUTED,
)
from backend import startup
from backend.routines import ActivityLog, RoutineStore, describe_days, suggest_routines
from backend.settings.settings_manager import SettingsManager
from backend.app_info import APP_NAME


def routine_text(routine):
    verb = {"studio": "Open", "launch": "Launch"}.get(routine["kind"], "Run")
    target = routine["target"] if routine["kind"] != "event" else f'"{routine["target"]}"'
    return f"{verb} {target} at {routine['time']} {describe_days(routine['days'])}"


class NotificationsPage(StudioPage):

    # Something changed (suggestion answered, routine paused...): the main
    # window refreshes the sidebar count and Home.
    changed = Signal()

    # A suggestion was accepted here (main window asks about background running).
    suggestion_accepted = Signal(dict)

    def __init__(self, parent=None):

        super().__init__(
            title="Notifications",
            subtitle=f"Suggestions and the things {APP_NAME} does for you.",
            parent=parent,
        )

        self.store = RoutineStore()

        self.setStyleSheet(self.styleSheet() + f"""
            QCheckBox {{ color: {PRIMARY_TEXT}; font-size: 14px; spacing: 10px; background: transparent; }}
            QCheckBox::indicator {{
                width: 18px; height: 18px; border-radius: 5px;
                border: 1px solid {BORDER}; background: {SURFACE};
            }}
            QCheckBox::indicator:checked {{ background: {PRIMARY}; border: 1px solid {PRIMARY}; }}
        """)

        self._heading("Suggestions")
        self.suggestions_layout = QVBoxLayout()
        self.suggestions_layout.setSpacing(8)
        self.content_layout.addLayout(self.suggestions_layout)

        self._heading("Your automations")
        self.routines_layout = QVBoxLayout()
        self.routines_layout.setSpacing(8)
        self.content_layout.addLayout(self.routines_layout)

        self._heading("Running on time")

        self.background = QCheckBox(f"Keep {APP_NAME} running in the system tray when I close it")
        self.background.toggled.connect(
            lambda on: SettingsManager().set_setting("run_in_background", bool(on))
        )
        self.content_layout.addWidget(self.background)

        self.at_login = QCheckBox(f"Start {APP_NAME} when I sign in to Windows")
        self.at_login.setEnabled(startup.is_supported())
        self.at_login.toggled.connect(self._on_at_login)
        self.content_layout.addWidget(self.at_login)

        note = QLabel(f"Automations only run while {APP_NAME} is open, so keep one of these on.")
        note.setWordWrap(True)
        note.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; background: transparent;")
        self.content_layout.addWidget(note)

        self.content_layout.addStretch()

        self.refresh()

    # -----------------------------------------------------

    def _heading(self, text):
        label = QLabel(text)
        label.setStyleSheet(f"""
            color: {PRIMARY_TEXT}; font-size: 17px; font-weight: 700;
            margin-top: 8px; border: none; background: transparent;
        """)
        self.content_layout.addWidget(label)

    @staticmethod
    def _button(text, color=PRIMARY_TEXT, primary=False):
        button = QPushButton(text)
        button.setCursor(Qt.PointingHandCursor)
        if primary:
            button.setStyleSheet(f"""
                QPushButton {{ background: {PRIMARY}; color: {ON_PRIMARY}; border: none;
                    border-radius: 8px; padding: 7px 14px; font-size: 12px; font-weight: 600; }}
                QPushButton:hover {{ background: {PRIMARY_HOVER}; }}
            """)
        else:
            button.setStyleSheet(f"""
                QPushButton {{ background: {OVERLAY_1}; color: {color};
                    border: 1px solid {BORDER}; border-radius: 8px;
                    padding: 7px 14px; font-size: 12px; font-weight: 600; }}
                QPushButton:hover {{ border: 1px solid {PRIMARY}; }}
            """)
        return button

    def _card(self):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 12px; }}
            QLabel {{ border: none; background: transparent; }}
        """)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(16, 12, 12, 12)
        return card, layout

    @staticmethod
    def _clear(layout):
        while layout.count():
            widget = layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()

    def _muted(self, text):
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px; background: transparent;")
        return label

    # -----------------------------------------------------

    def pending_suggestions(self):
        self.store.load()
        try:
            return suggest_routines(ActivityLog().entries(), self.store)
        except Exception as e:
            print(f"⚠ Could not check for routines: {e}")
            return []

    def refresh(self):

        suggestions = self.pending_suggestions()

        self._clear(self.suggestions_layout)

        if not suggestions:
            self.suggestions_layout.addWidget(self._muted(
                "Nothing new. When you do the same thing around the same time "
                f"on most days, {APP_NAME} will offer to do it for you."
            ))

        for s in suggestions:
            card, layout = self._card()
            text = QLabel(s["message"])
            text.setWordWrap(True)
            text.setStyleSheet(f"color: {PRIMARY_TEXT}; font-size: 14px;")
            layout.addWidget(text, 1)

            automate = self._button(f"Automate at {s['time']}", primary=True)
            automate.clicked.connect(lambda checked=False, s=s: self._accept(s))
            layout.addWidget(automate)

            dismiss = self._button("Dismiss")
            dismiss.setToolTip("Hide this suggestion for 30 days")
            dismiss.clicked.connect(lambda checked=False, s=s: self._dismiss(s))
            layout.addWidget(dismiss)

            self.suggestions_layout.addWidget(card)

        self._clear(self.routines_layout)

        if not self.store.routines:
            self.routines_layout.addWidget(self._muted("No automations yet."))

        for routine in self.store.routines:
            self.routines_layout.addWidget(self._routine_row(routine))

        for box, value in (
            (self.background, bool(SettingsManager().get_setting("run_in_background"))),
            (self.at_login, startup.is_enabled()),
        ):
            box.blockSignals(True)
            box.setChecked(value)
            box.blockSignals(False)

    def _routine_row(self, routine):

        card, layout = self._card()
        enabled = routine.get("enabled", True)

        text = QLabel(routine_text(routine))
        text.setStyleSheet(f"color: {PRIMARY_TEXT if enabled else TEXT_MUTED}; font-size: 14px;")
        layout.addWidget(text, 1)

        toggle = self._button("Pause" if enabled else "Resume")
        toggle.setAccessibleName(f"{'Pause' if enabled else 'Resume'}: {routine_text(routine)}")
        toggle.clicked.connect(
            lambda checked=False, r=routine: self._set_enabled(r["id"], not r.get("enabled", True))
        )
        layout.addWidget(toggle)

        delete = self._button("Delete", ERROR)
        delete.setAccessibleName(f"Delete: {routine_text(routine)}")
        delete.clicked.connect(lambda checked=False, r=routine: self._delete(r))
        layout.addWidget(delete)

        return card

    # -----------------------------------------------------

    def _accept(self, suggestion):
        self.store.add(suggestion)
        self.suggestion_accepted.emit(suggestion)
        self.refresh()
        self.changed.emit()

    def _dismiss(self, suggestion):
        self.store.decline(suggestion)
        self.refresh()
        self.changed.emit()

    def _set_enabled(self, routine_id, enabled):
        self.store.set_enabled(routine_id, enabled)
        self.refresh()
        self.changed.emit()

    def _delete(self, routine):
        answer = QMessageBox.question(
            self, "Delete Automation", f"Stop doing this automatically?\n\n{routine_text(routine)}"
        )
        if answer == QMessageBox.Yes:
            self.store.remove(routine["id"])
            self.refresh()
            self.changed.emit()

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

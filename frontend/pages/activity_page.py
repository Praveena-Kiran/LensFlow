"""
History page: what Wield has done recently (opened studios, events run by
click, gesture or routine), with a button to clear it. Stored only on this
computer. Automations themselves live on the Notifications page.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
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
    OVERLAY_1,
    PRIMARY,
    PRIMARY_TEXT,
    SECONDARY_TEXT,
    TEXT_MUTED,
)
from backend.routines import ActivityLog
from backend.app_info import APP_NAME


RECENT_LIMIT = 50

KIND_VERBS = {
    "studio": "Opened",
    "launch": "Launched",
    "event": "Ran",
}

TRIGGER_NOTES = {
    "gesture": "by gesture",
    "routine": "by automation",
    "click": "",
}


class ActivityPage(StudioPage):

    def __init__(self, parent=None):

        super().__init__(
            title="History",
            subtitle=f"What {APP_NAME} has done. Stored only on this computer, for up to 90 days.",
            parent=parent,
        )

        self.log = ActivityLog()

        header = QHBoxLayout()

        heading = QLabel("Recent activity")
        heading.setStyleSheet(f"""
            color: {PRIMARY_TEXT}; font-size: 17px; font-weight: 700;
            border: none; background: transparent;
        """)
        header.addWidget(heading)
        header.addStretch()

        clear = QPushButton("Clear history")
        clear.setCursor(Qt.PointingHandCursor)
        clear.setStyleSheet(f"""
            QPushButton {{
                background: {OVERLAY_1}; color: {ERROR};
                border: 1px solid {BORDER}; border-radius: 8px;
                padding: 7px 14px; font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ border: 1px solid {PRIMARY}; }}
        """)
        clear.clicked.connect(self._clear_history)
        header.addWidget(clear)

        self.content_layout.addLayout(header)

        self.recent_layout = QVBoxLayout()
        self.recent_layout.setSpacing(0)
        self.content_layout.addLayout(self.recent_layout)

        self.content_layout.addStretch()

        self.refresh()

    def refresh(self):

        while self.recent_layout.count():
            widget = self.recent_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()

        entries = sorted(self.log.entries(), key=lambda e: e["_at"], reverse=True)[:RECENT_LIMIT]

        if not entries:
            empty = QLabel("Nothing yet.")
            empty.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px; background: transparent;")
            self.recent_layout.addWidget(empty)

        for entry in entries:
            self.recent_layout.addWidget(self._activity_row(entry))

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

    def _clear_history(self):
        answer = QMessageBox.question(
            self,
            "Clear History",
            f"Delete everything {APP_NAME} has recorded about what you open and "
            "when? Your automations are kept.",
        )
        if answer == QMessageBox.Yes:
            self.log.clear()
            self.refresh()

    def showEvent(self, event):
        self.refresh()
        super().showEvent(event)

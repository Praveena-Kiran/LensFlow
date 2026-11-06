"""
The routine suggestion shown when LensFlow opens. "Automate" accepts it;
"Not now" just closes it, and the suggestion waits in Notifications.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from frontend.styles.theme import (
    BG_DARK,
    BORDER,
    ON_PRIMARY,
    OVERLAY_1,
    PRIMARY,
    PRIMARY_HOVER,
    PRIMARY_TEXT,
    SECONDARY_TEXT,
    TEXT_MUTED,
)
from backend.app_info import APP_NAME


class SuggestionDialog(QDialog):

    def __init__(self, suggestion, parent=None):

        super().__init__(parent)

        self.suggestion = suggestion

        self.setWindowTitle("Suggested routine")
        self.setModal(True)
        self.setMinimumWidth(440)
        self.setStyleSheet(f"""
            QDialog {{ background: {BG_DARK}; border: 1px solid {BORDER}; }}
            QLabel {{ background: transparent; border: none; }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 24)
        layout.setSpacing(10)

        eyebrow = QLabel("SUGGESTED ROUTINE")
        eyebrow.setStyleSheet(f"color: {PRIMARY}; font-size: 11px; font-weight: 700; letter-spacing: 1px;")
        layout.addWidget(eyebrow)

        message = QLabel(suggestion["message"])
        message.setWordWrap(True)
        message.setAccessibleName("Suggested routine")
        message.setStyleSheet(f"color: {PRIMARY_TEXT}; font-size: 17px; font-weight: 500;")
        layout.addWidget(message)

        detail = QLabel(
            f"Spotted on {suggestion['hits']} of the last {suggestion['of']} days you "
            f"used {APP_NAME}. What {APP_NAME} learns stays on this computer."
        )
        detail.setWordWrap(True)
        detail.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(detail)

        layout.addSpacing(12)

        buttons = QHBoxLayout()
        buttons.addStretch()

        later = QPushButton("Not now")
        later.setCursor(Qt.PointingHandCursor)
        later.setToolTip("You can automate it later from Notifications")
        later.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {SECONDARY_TEXT}; border: none;
                border-radius: 10px; padding: 10px 14px; font-size: 13px; }}
            QPushButton:hover {{ color: {PRIMARY_TEXT}; background: {OVERLAY_1}; }}
        """)
        later.clicked.connect(self.reject)

        automate = QPushButton(f"Automate at {suggestion['time']}")
        automate.setCursor(Qt.PointingHandCursor)
        automate.setDefault(True)
        automate.setStyleSheet(f"""
            QPushButton {{ background: {PRIMARY}; color: {ON_PRIMARY}; border: none;
                border-radius: 10px; padding: 10px 18px; font-size: 13px; font-weight: 600; }}
            QPushButton:hover {{ background: {PRIMARY_HOVER}; }}
        """)
        automate.clicked.connect(self.accept)

        buttons.addWidget(later)
        buttons.addWidget(automate)
        layout.addLayout(buttons)

        hint = QLabel("Not now keeps it in Notifications.")
        hint.setAlignment(Qt.AlignRight)
        hint.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(hint)

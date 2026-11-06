"""
A quiet banner that offers to automate something the user does routinely.
Hidden until there is a suggestion; nothing is automated unless they click
"Automate".
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from frontend.styles.theme import (
    BORDER,
    PRIMARY,
    PRIMARY_MUTED,
    PRIMARY_TEXT,
    SECONDARY_TEXT,
    SURFACE,
    TEXT_MUTED,
)


class SuggestionBanner(QFrame):

    accepted = Signal(dict)
    declined = Signal(dict)

    def __init__(self, parent=None):

        super().__init__(parent)

        self.suggestion = None

        self.setObjectName("SuggestionBanner")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            QFrame#SuggestionBanner {{
                background: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 16px;
            }}
            QLabel {{ background: transparent; border: none; }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 16, 16)
        layout.setSpacing(16)

        text = QVBoxLayout()
        text.setSpacing(4)

        eyebrow = QLabel("SUGGESTED ROUTINE")
        eyebrow.setStyleSheet(
            f"color: {PRIMARY}; font-size: 11px; font-weight: 700; letter-spacing: 1px;"
        )
        text.addWidget(eyebrow)

        self.message = QLabel("")
        self.message.setWordWrap(True)
        self.message.setAccessibleName("Suggested routine")
        self.message.setStyleSheet(f"color: {PRIMARY_TEXT}; font-size: 15px;")
        text.addWidget(self.message)

        privacy = QLabel("What LensFlow learns stays on this computer.")
        privacy.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        text.addWidget(privacy)

        layout.addLayout(text, 1)

        self.automate = QPushButton("Automate")
        self.automate.setCursor(Qt.PointingHandCursor)
        self.automate.setStyleSheet(f"""
            QPushButton {{
                background: {PRIMARY_MUTED}; color: {PRIMARY_TEXT};
                border: 1px solid {PRIMARY}; border-radius: 10px;
                padding: 10px 16px; font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {PRIMARY}; }}
        """)
        self.automate.clicked.connect(self._accept)

        self.not_now = QPushButton("Not now")
        self.not_now.setCursor(Qt.PointingHandCursor)
        self.not_now.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {SECONDARY_TEXT};
                border: none; border-radius: 10px;
                padding: 10px 14px; font-size: 13px;
            }}
            QPushButton:hover {{ color: {PRIMARY_TEXT}; }}
        """)
        self.not_now.clicked.connect(self._decline)

        layout.addWidget(self.automate, 0, Qt.AlignVCenter)
        layout.addWidget(self.not_now, 0, Qt.AlignVCenter)

        self.hide()

    def show_suggestion(self, suggestion):

        self.suggestion = suggestion

        if suggestion is None:
            self.hide()
            return

        self.message.setText(suggestion["message"])
        self.automate.setText(f"Automate at {suggestion['time']}")
        self.show()

    def _accept(self):
        if self.suggestion:
            self.accepted.emit(self.suggestion)
        self.show_suggestion(None)

    def _decline(self):
        if self.suggestion:
            self.declined.emit(self.suggestion)
        self.show_suggestion(None)

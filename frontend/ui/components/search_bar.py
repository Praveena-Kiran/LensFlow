"""LensFlow Design System - SearchBar Component

Rounded search input with embedded search icon, animated focus glow effect, and clear button.
"""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLineEdit, QPushButton, QWidget
from frontend.ui.components.icons import VectorIcon
from frontend.ui.styles.colors import SURFACE, ELEVATED, ACCENT, TEXT_PRIMARY, TEXT_MUTED, BORDER
from frontend.ui.styles.spacing import RADIUS_FULL, SPACE_16
from frontend.ui.styles.constants import SEARCH_BAR_HEIGHT


class SearchBar(QFrame):
    """Rounded search bar widget with animated focus ring and search icon."""

    textChanged = Signal(str)

    def __init__(self, placeholder: str = "Search workspaces, studios, commands...", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedHeight(SEARCH_BAR_HEIGHT)
        self.setObjectName("SearchBar")

        # Container Layout
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(14, 0, 10, 0)
        self._layout.setSpacing(10)

        # Search Vector Icon
        self.search_icon = VectorIcon(icon_type=VectorIcon.SEARCH, color=TEXT_MUTED, size=18)
        self._layout.addWidget(self.search_icon, 0, Qt.AlignmentFlag.AlignCenter)

        # QLineEdit Input Field
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(placeholder)
        self.input_field.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #FFFFFF;
                font-size: 13px;
                padding: 0px;
            }
        """)
        self.input_field.textChanged.connect(self._on_text_changed)
        self.input_field.textChanged.connect(self.textChanged.emit)
        self._layout.addWidget(self.input_field, 1)

        # Clear Button
        self.clear_button = QPushButton("✕")
        self.clear_button.setFixedSize(20, 20)
        self.clear_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_button.hide()
        self.clear_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #6B7280;
                border: none;
                font-size: 11px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
                color: #FFFFFF;
            }
        """)
        self.clear_button.clicked.connect(self.clear)
        self._layout.addWidget(self.clear_button, 0, Qt.AlignmentFlag.AlignCenter)

        self._apply_style(focused=False)

    def text(self) -> str:
        """Returns the current search query text."""
        return self.input_field.text()

    def set_text(self, text: str):
        """Sets the search query text."""
        self.input_field.setText(text)

    def clear(self):
        """Clears search input field."""
        self.input_field.clear()

    def focusInEvent(self, event):
        self._apply_style(focused=True)
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self._apply_style(focused=False)
        super().focusOutEvent(event)

    def _on_text_changed(self, text: str):
        self.clear_button.setVisible(bool(text))

    def _apply_style(self, focused: bool):
        border_style = f"1px solid {ACCENT}" if focused else f"1px solid {BORDER}"
        bg_style = ELEVATED if focused else SURFACE
        icon_color = ACCENT if focused else TEXT_MUTED
        self.search_icon.set_color(icon_color)

        self.setStyleSheet(f"""
            QFrame#SearchBar {{
                background-color: {bg_style};
                border: {border_style};
                border-radius: 21px;
            }}
        """)

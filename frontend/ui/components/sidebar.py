"""LensFlow Design System - Sidebar Component

Collapsible modern sidebar navigation component supporting dynamic menu item registration,
smooth animation transitions, outline icons, and hover feedback without hardcoded pages.
"""

from typing import Optional, Dict, Callable
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QScrollArea, QSizePolicy
)
from frontend.ui.styles.colors import SURFACE, ACCENT, TEXT_PRIMARY, TEXT_SECONDARY, BORDER
from frontend.ui.styles.spacing import SPACE_8, SPACE_16, RADIUS_MD
from frontend.ui.styles.constants import (
    SIDEBAR_COLLAPSED_WIDTH, SIDEBAR_EXPANDED_WIDTH, ANIM_NORMAL, EASING_DEFAULT
)
from frontend.ui.components.icons import VectorIcon


class SidebarMenuItem(QPushButton):
    """Individual sidebar navigation item button."""

    def __init__(self, item_id: str, label: str, icon_type: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.item_id = item_id
        self.label_text = label
        self.icon_type = icon_type
        self.is_active = False

        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(44)

        # Layout inside button
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(12, 0, 12, 0)
        self._layout.setSpacing(SPACE_16)

        # Icon
        self.icon_widget = VectorIcon(icon_type=icon_type, color=TEXT_SECONDARY, size=20)
        self._layout.addWidget(self.icon_widget)

        # Label
        self.label_widget = QLabel(label)
        self.label_widget.setStyleSheet(f"color: {TEXT_SECONDARY}; font-weight: 500; font-size: 13px;")
        self._layout.addWidget(self.label_widget, 1)

        self._apply_style()

    def set_active(self, active: bool):
        self.is_active = active
        self.setChecked(active)
        color = TEXT_PRIMARY if active else TEXT_SECONDARY
        icon_color = ACCENT if active else TEXT_SECONDARY
        self.icon_widget.set_color(icon_color)
        self.label_widget.setStyleSheet(f"color: {color}; font-weight: {'600' if active else '500'}; font-size: 13px;")
        self._apply_style()

    def set_expanded_text_visible(self, visible: bool):
        self.label_widget.setVisible(visible)

    def _apply_style(self):
        bg_color = "rgba(59, 130, 246, 0.15)" if self.is_active else "transparent"
        border_left = f"3px solid {ACCENT}" if self.is_active else "3px solid transparent"

        self.setStyleSheet(f"""
            SidebarMenuItem {{
                background-color: {bg_color};
                border-left: {border_left};
                border-radius: {RADIUS_MD}px;
                text-align: left;
            }}
            SidebarMenuItem:hover {{
                background-color: rgba(255, 255, 255, 0.06);
            }}
        """)


class Sidebar(QFrame):
    """Collapsible reusable sidebar navigation panel."""

    item_selected = Signal(str)

    def __init__(self, is_collapsed: bool = True, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.is_collapsed = is_collapsed
        self.menu_items: Dict[str, SidebarMenuItem] = {}
        self.active_item_id: Optional[str] = None

        self.setObjectName("Sidebar")
        initial_width = SIDEBAR_COLLAPSED_WIDTH if is_collapsed else SIDEBAR_EXPANDED_WIDTH
        self.setFixedWidth(initial_width)

        # Main Layout
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(SPACE_8, SPACE_16, SPACE_8, SPACE_16)
        self._layout.setSpacing(SPACE_8)

        # Top Header / Collapse Toggle Button
        self._header_layout = QHBoxLayout()
        self._header_layout.setContentsMargins(4, 0, 4, 0)

        self.toggle_button = QPushButton()
        self.toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_button.setFixedSize(40, 40)
        self.toggle_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.08);
            }
        """)
        toggle_icon_layout = QHBoxLayout(self.toggle_button)
        toggle_icon_layout.setContentsMargins(0, 0, 0, 0)
        self.toggle_icon = VectorIcon(icon_type=VectorIcon.SIDEBAR_TOGGLE, color=TEXT_SECONDARY, size=20)
        toggle_icon_layout.addWidget(self.toggle_icon, 0, Qt.AlignmentFlag.AlignCenter)
        self.toggle_button.clicked.connect(self.toggle_collapse)

        self._header_layout.addWidget(self.toggle_button, 0, Qt.AlignmentFlag.AlignCenter)
        self._layout.addLayout(self._header_layout)

        # Scroll Area for Menu Items
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.items_container = QWidget()
        self.items_layout = QVBoxLayout(self.items_container)
        self.items_layout.setContentsMargins(0, 8, 0, 0)
        self.items_layout.setSpacing(4)
        self.items_layout.addStretch()

        self.scroll_area.setWidget(self.items_container)
        self._layout.addWidget(self.scroll_area, 1)

        # Width Animation Setup
        self._anim = QPropertyAnimation(self, b"maximumWidth", self)
        self._anim.setDuration(ANIM_NORMAL)
        self._anim.setEasingCurve(EASING_DEFAULT)

        self._apply_style()
        self._update_item_text_visibility()

    def add_menu_item(
        self,
        item_id: str,
        label: str,
        icon_type: str = VectorIcon.GRID,
        callback: Optional[Callable[[], None]] = None
    ):
        """Dynamically adds a menu item to the sidebar."""
        item = SidebarMenuItem(item_id, label, icon_type, self)
        item.set_expanded_text_visible(not self.is_collapsed)

        def _on_click():
            self.select_item(item_id)
            if callback:
                callback()

        item.clicked.connect(_on_click)

        # Insert before stretch
        self.items_layout.insertWidget(self.items_layout.count() - 1, item)
        self.menu_items[item_id] = item

        # Select first added item by default
        if len(self.menu_items) == 1:
            self.select_item(item_id)

    def select_item(self, item_id: str):
        """Sets active menu item by ID."""
        if item_id in self.menu_items:
            for i_id, item in self.menu_items.items():
                item.set_active(i_id == item_id)
            self.active_item_id = item_id
            self.item_selected.emit(item_id)

    def toggle_collapse(self):
        """Toggles sidebar between collapsed (64px) and expanded (240px)."""
        self.set_collapsed(not self.is_collapsed)

    def set_collapsed(self, collapsed: bool):
        self.is_collapsed = collapsed
        target_width = SIDEBAR_COLLAPSED_WIDTH if collapsed else SIDEBAR_EXPANDED_WIDTH

        self.setMinimumWidth(SIDEBAR_COLLAPSED_WIDTH)
        self._anim.stop()
        self._anim.setStartValue(self.width())
        self._anim.setEndValue(target_width)

        def _on_finish():
            self.setFixedWidth(target_width)
            self._update_item_text_visibility()
            try:
                self._anim.finished.disconnect(_on_finish)
            except RuntimeError:
                pass

        self._anim.finished.connect(_on_finish)
        self._anim.start()

    def _update_item_text_visibility(self):
        for item in self.menu_items.values():
            item.set_expanded_text_visible(not self.is_collapsed)

    def _apply_style(self):
        self.setStyleSheet(f"""
            QFrame#Sidebar {{
                background-color: {SURFACE};
                border-right: 1px solid {BORDER};
            }}
        """)

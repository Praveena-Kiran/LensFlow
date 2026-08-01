from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSpacerItem, QSizePolicy, QWidget
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Signal
from ui.theme import BG_SIDEBAR, BORDER_COLOR, ACCENT, TEXT_PRIMARY, TEXT_MUTED, get_font

class SidebarButton(QWidget):
    clicked = Signal(int)
    
    def __init__(self, index, icon, text, coming_soon=False, parent=None):
        super().__init__(parent)
        self.index = index
        self.icon = icon
        self.text = text
        self.coming_soon = coming_soon
        self.active = False
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(12, 0, 12, 0)
        self.layout.setSpacing(12)
        
        # Icon label
        self.icon_label = QLabel(icon)
        self.icon_label.setFont(get_font(13))
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedWidth(24)
        
        # Text label
        self.text_label = QLabel(text)
        self.text_label.setFont(get_font(10, bold=True))
        self.text_label.setStyleSheet(f"color: {TEXT_MUTED};")
        self.text_label.setVisible(False)
        
        self.layout.addWidget(self.icon_label)
        self.layout.addWidget(self.text_label, 1)
        
        # Badge for Coming Soon
        if coming_soon:
            self.badge = QLabel("Soon")
            self.badge.setFont(get_font(8, bold=True))
            self.badge.setStyleSheet(f"""
                background-color: #27272A;
                color: {ACCENT};
                border-radius: 4px;
                padding: 2px 6px;
            """)
            self.badge.setVisible(False)
            self.layout.addWidget(self.badge)
            self.setToolTip("Coming Soon")
            
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(48)
        self.update_style()

    def update_style(self):
        if self.active:
            bg = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(124, 58, 237, 0.25), stop:1 rgba(6, 182, 212, 0.1))"
            border = f"1px solid {ACCENT}"
            text_color = "#FFFFFF"
            icon_style = f"color: {ACCENT}; font-size: 14px;"
        else:
            bg = "transparent"
            border = "none"
            text_color = TEXT_MUTED
            icon_style = f"color: {TEXT_MUTED};"
            
        if self.coming_soon:
            text_color = "#475569"
            icon_style = "color: #475569;"
            
        self.setStyleSheet(f"""
            QWidget {{
                background: {bg};
                border-radius: 10px;
                border: {border};
            }}
            QLabel {{
                border: none;
                background-color: transparent;
                color: {text_color};
            }}
        """)
        self.icon_label.setStyleSheet(icon_style)
        
    def set_active(self, active):
        if not self.coming_soon:
            self.active = active
            self.update_style()
            
    def set_expanded(self, expanded):
        self.text_label.setVisible(expanded)
        if self.coming_soon:
            self.badge.setVisible(expanded)
            
    def mousePressEvent(self, event):
        if not self.coming_soon:
            self.clicked.emit(self.index)
        super().mousePressEvent(event)
        
    def enterEvent(self, event):
        if not self.active and not self.coming_soon:
            self.setStyleSheet(f"""
                QWidget {{
                    background-color: #121829;
                    border-radius: 10px;
                    border: 1px solid #1E293B;
                }}
                QLabel {{
                    color: #F8FAFC;
                }}
            """)
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.update_style()
        super().leaveEvent(event)


class Sidebar(QFrame):
    tab_changed = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        self.setMinimumWidth(72)
        self.setMaximumWidth(72)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_SIDEBAR};
                border-right: 1px solid {BORDER_COLOR};
            }}
        """)
        
        # Animations
        self.width_anim = QPropertyAnimation(self, b"minimumWidth")
        self.width_anim.setDuration(220)
        self.width_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        self.width_anim_max = QPropertyAnimation(self, b"maximumWidth")
        self.width_anim_max.setDuration(220)
        self.width_anim_max.setEasingCurve(QEasingCurve.OutCubic)
        
        self.is_expanded = False
        
        # Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 20, 10, 20)
        self.main_layout.setSpacing(8)
        
        # Header / Brand Logo
        self.brand_layout = QHBoxLayout()
        self.brand_layout.setContentsMargins(12, 0, 12, 10)
        self.brand_icon = QLabel("🌀")
        self.brand_icon.setFont(get_font(18))
        self.brand_icon.setAlignment(Qt.AlignCenter)
        self.brand_text = QLabel("LensFlow")
        self.brand_text.setFont(get_font(14, bold=True))
        self.brand_text.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none; background: transparent;")
        self.brand_text.setVisible(False)
        self.brand_layout.addWidget(self.brand_icon)
        self.brand_layout.addWidget(self.brand_text, 1)
        self.main_layout.addLayout(self.brand_layout)
        
        # Navigation Items
        self.buttons = []
        nav_items = [
            (0, "🏠", "Home"),
            (1, "⚡", "Flows"),
            (2, "👤", "Profiles"),
            (3, "✋", "Live"),
            (4, "⚙", "Settings")
        ]
        
        for index, icon, text, *coming_soon in nav_items:
            is_soon = coming_soon[0] if coming_soon else False
            btn = SidebarButton(index, icon, text, coming_soon=is_soon)
            btn.clicked.connect(self.on_btn_clicked)
            self.buttons.append(btn)
            self.main_layout.addWidget(btn)
            
        # Spacer
        self.main_layout.addStretch()
        
        # Bottom Section - Avatar & Version
        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setContentsMargins(8, 10, 8, 0)
        
        # Avatar Container
        self.avatar_container = QWidget()
        self.avatar_container.setFixedSize(40, 40)
        self.avatar_container.setStyleSheet("""
            background-color: #3F3F46;
            border-radius: 20px;
        """)
        
        avatar_layout = QHBoxLayout(self.avatar_container)
        avatar_layout.setContentsMargins(0, 0, 0, 0)
        self.avatar_label = QLabel("P")
        self.avatar_label.setFont(get_font(11, bold=True))
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.avatar_label.setStyleSheet("color: #FFFFFF; border: none;")
        avatar_layout.addWidget(self.avatar_label)
        
        # User Info text
        self.user_info_layout = QVBoxLayout()
        self.user_info_layout.setSpacing(2)
        self.user_info_layout.setContentsMargins(0, 0, 0, 0)
        self.user_name = QLabel("Praveena")
        self.user_name.setFont(get_font(9, bold=True))
        self.user_name.setStyleSheet("color: white; border: none; background: transparent;")
        self.user_name.setVisible(False)
        self.user_status = QLabel("Active")
        self.user_status.setFont(get_font(8))
        self.user_status.setStyleSheet("color: #22C55E; border: none; background: transparent;")
        self.user_status.setVisible(False)
        self.user_info_layout.addWidget(self.user_name)
        self.user_info_layout.addWidget(self.user_status)
        
        self.bottom_layout.addWidget(self.avatar_container)
        self.bottom_layout.addLayout(self.user_info_layout, 1)
        self.main_layout.addLayout(self.bottom_layout)
        
        # Version Label
        self.version_label = QLabel("v0.1.0")
        self.version_label.setFont(get_font(8))
        self.version_label.setStyleSheet(f"color: {TEXT_MUTED}; border: none; background: transparent;")
        self.version_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.version_label)
        
        # Activate home tab by default
        self.buttons[0].set_active(True)
        
    def expand_sidebar(self):
        if not self.is_expanded:
            self.is_expanded = True
            
            # Show text elements before animation finishes so it fills out nicely
            self.brand_text.setVisible(True)
            for btn in self.buttons:
                btn.set_expanded(True)
            self.user_name.setVisible(True)
            self.user_status.setVisible(True)
            self.version_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.version_label.setContentsMargins(15, 0, 0, 0)
            
            self.width_anim.stop()
            self.width_anim.setStartValue(72)
            self.width_anim.setEndValue(200)
            self.width_anim.start()
            
            self.width_anim_max.stop()
            self.width_anim_max.setStartValue(72)
            self.width_anim_max.setEndValue(200)
            self.width_anim_max.start()
            
    def collapse_sidebar(self):
        if self.is_expanded:
            self.is_expanded = False
            
            # Hide texts immediately on collapse trigger to keep it neat
            self.brand_text.setVisible(False)
            for btn in self.buttons:
                btn.set_expanded(False)
            self.user_name.setVisible(False)
            self.user_status.setVisible(False)
            self.version_label.setAlignment(Qt.AlignCenter)
            self.version_label.setContentsMargins(0, 0, 0, 0)
            
            self.width_anim.stop()
            self.width_anim.setStartValue(200)
            self.width_anim.setEndValue(72)
            self.width_anim.start()
            
            self.width_anim_max.stop()
            self.width_anim_max.setStartValue(200)
            self.width_anim_max.setEndValue(72)
            self.width_anim_max.start()

    def enterEvent(self, event):
        self.expand_sidebar()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.collapse_sidebar()
        super().leaveEvent(event)
        
    def on_btn_clicked(self, index):
        for btn in self.buttons:
            btn.set_active(btn.index == index)
        self.tab_changed.emit(index)

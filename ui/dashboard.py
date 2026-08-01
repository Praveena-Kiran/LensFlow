from mediapipe.tasks.cc.vision.gesture_recognizer.proto import gesture_classifier_graph_options_pb2
from mediapipe.tasks.cc.vision.gesture_recognizer.proto import gesture_classifier_graph_options_pb2
from backend import studios
from backend.studios import studio_manager
from cv2 import wechat_qrcode
from PySide6.QtWidgets import QPushButton
import math
import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, 
    QFrame, QComboBox, QSlider, QScrollArea, QLineEdit, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QPainterPath
from ui.theme import (
    HoverCard, ModernButton, BG_PRIMARY, BG_CARD, BORDER_COLOR, 
    ACCENT, ACCENT_HOVER, SUCCESS, TEXT_PRIMARY, TEXT_MUTED, get_font, WARM_AMBER, WARM_ROSE
)
from ui.right_panel import RightPanel
from backend.studios.studio_manager import StudioManager
from backend.automation.flow_manager import FlowManager
from ui.dialogs.create_studio_dialog import CreateStudioDialog
from ui.dialogs.studio_settings_dialog import StudioSettingsDialog
from ui.camera_thread import CameraThread
from ui.theme_manager import get_theme


# --- APP PILL ---

class AppPill(QLabel):
    """
    A small badged app icon/label inside Studio cards.
    """
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.studio_manager = StudioManager()
        self.flow_manager = FlowManager()
        self.setFont(get_font(8, bold=True))
        self.setStyleSheet(f"""
            QLabel {{
                background-color: #1F2937;
                color: #D1D5DB;
                border: 1px solid {BORDER_COLOR};
                border-radius: 6px;
                padding: 3px 8px;
            }}
        """)


# --- STUDIO CARD ---

class StudioCard(QFrame):
    """
    A premium floating Studio card featuring micro-interactions,
    active apps, and linear gradient trigger actions.
    """
    clicked = Signal(str)  # Emits Studio name when the primary action is clicked
    settings_clicked = Signal(str)

    def __init__(self, name, icon, desc, apps, last_used="", is_create_card=False, parent=None):
        super().__init__(parent)
        self.name = name
        self.icon = icon
        self.is_create_card = is_create_card
        
        # Subtle Drop Shadow
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(16)
        self.shadow.setColor(QColor(0, 0, 0, 80))
        self.shadow.setOffset(0, 4)
        self.setGraphicsEffect(self.shadow)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(18, 18, 18, 18)
        self.layout.setSpacing(12)
        
        if is_create_card:
            self.set_create_style()
            self.layout.setAlignment(Qt.AlignCenter)
            
            icon_lbl = QLabel(icon)
            icon_lbl.setFont(get_font(24))
            icon_lbl.setAlignment(Qt.AlignCenter)
            
            name_lbl = QLabel(name)
            name_lbl.setFont(get_font(12, bold=True))
            name_lbl.setStyleSheet(f"color: {ACCENT};")
            name_lbl.setAlignment(Qt.AlignCenter)
            
            desc_lbl = QLabel(desc)
            desc_lbl.setFont(get_font(9))
            desc_lbl.setStyleSheet(f"color: {TEXT_MUTED};")
            desc_lbl.setAlignment(Qt.AlignCenter)
            desc_lbl.setWordWrap(True)
            
            self.layout.addStretch()
            self.layout.addWidget(icon_lbl)
            self.layout.addWidget(name_lbl)
            self.layout.addWidget(desc_lbl)
            self.layout.addStretch()
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.set_normal_style()
            
            # Header Row
            header = QHBoxLayout()
            header.setSpacing(8)
            icon_lbl = QLabel(icon)
            icon_lbl.setFont(get_font(14))
            name_lbl = QLabel(name)
            name_lbl.setFont(get_font(11, bold=True))
            name_lbl.setStyleSheet("color: white;")
            header.addWidget(icon_lbl)
            header.addWidget(name_lbl)
            header.addStretch()
            self.btn_settings = QPushButton("⚙")
            self.btn_settings.setFixedSize(28, 28)
            header.addWidget(self.btn_settings)
            self.btn_settings.clicked.connect(self.open_settings)
            self.layout.addLayout(header)
            
            # Subtitle Description
            desc_lbl = QLabel(desc)
            desc_lbl.setFont(get_font(9))
            desc_lbl.setStyleSheet(f"color: {TEXT_MUTED};")
            desc_lbl.setWordWrap(True)
            self.layout.addWidget(desc_lbl)
            
            # Integrated Apps Row
            apps_lay = QHBoxLayout()
            apps_lay.setSpacing(6)
            apps_lay.setAlignment(Qt.AlignLeft)
            for app in apps:
                pill = AppPill(app)
                apps_lay.addWidget(pill)
            self.layout.addLayout(apps_lay)
            
            # Footer Row
            footer = QHBoxLayout()
            last_lbl = QLabel(last_used)
            last_lbl.setFont(get_font(8))
            last_lbl.setStyleSheet(f"color: {TEXT_MUTED};")
            
            # Customize action button copy based on studio
            action_text = "Enter Studio →"
            if name == "Gaming":
                action_text = "Play →"
            elif name == "Study":
                action_text = "Focus →"
            elif name == "Presentation":
                action_text = "Present →"
                
            self.btn_action = ModernButton(action_text, gradient=True)
            self.btn_action.setFixedHeight(30)
            self.btn_action.clicked.connect(self.on_btn_clicked)
            
            footer.addWidget(last_lbl)
            footer.addStretch()
            footer.addWidget(self.btn_action)
            self.layout.addLayout(footer)
            
    def on_btn_clicked(self):
        self.clicked.emit(self.name)
        
    def set_normal_style(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border-radius: 14px;
                border: 1px solid {BORDER_COLOR};
            }}
        """)
        
    def set_hover_style(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #2D2D30;
                border-radius: 14px;
                border: 1px solid {ACCENT};
            }}
        """)
        
    def set_create_style(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border-radius: 14px;
                border: 2px dashed {BORDER_COLOR};
            }}
        """)
        
    def set_create_hover_style(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #1F1F23;
                border-radius: 14px;
                border: 2px dashed {ACCENT};
            }}
        """)
        
    def enterEvent(self, event):
        if self.is_create_card:
            self.set_create_hover_style()
            self.shadow.setColor(QColor(124, 58, 237, 40))
        else:
            self.set_hover_style()
            self.shadow.setColor(QColor(124, 58, 237, 50))
            
        self.shadow.setBlurRadius(24)
        self.shadow.setOffset(0, 6)
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        if self.is_create_card:
            self.set_create_style()
        else:
            self.set_normal_style()
            
        self.shadow.setBlurRadius(16)
        self.shadow.setColor(QColor(0, 0, 0, 80))
        self.shadow.setOffset(0, 4)
        super().leaveEvent(event)
        
    def mousePressEvent(self, event):
        if self.is_create_card:
            self.clicked.emit("CreateStudio")
        super().mousePressEvent(event)

    def open_settings(self):
        self.settings_clicked.emit(self.name)


# --- TOP BAR ---

class TopBar(QWidget):
    """
    Futuristic top bar containing LensFlow logo, accessibility tagline,
    system state indicator (ACTIVE/STANDBY), and user profile.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(68)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 8, 30, 8)
        layout.setSpacing(20)
        
        # Branding Header
        brand_box = QVBoxLayout()
        brand_box.setSpacing(2)
        
        logo_lay = QHBoxLayout()
        logo_lay.setSpacing(8)
        
        emblem = QLabel("🌀")
        emblem.setFont(get_font(14))
        
        logo = QLabel("LensFlow")
        logo.setFont(get_font(15, bold=True))
        logo.setStyleSheet("color: #FFFFFF; letter-spacing: 0.5px;")
        
        badge_ai = QLabel("AI ACCESSIBILITY")
        badge_ai.setFont(get_font(7, bold=True))
        badge_ai.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7C3AED, stop:1 #06B6D4); color: white; border-radius: 4px; padding: 2px 7px;")
        
        logo_lay.addWidget(emblem)
        logo_lay.addWidget(logo)
        logo_lay.addWidget(badge_ai)
        logo_lay.addStretch()
        
        tagline = QLabel("Gesture-powered interaction for a more accessible digital world")
        tagline.setFont(get_font(8, bold=False))
        tagline.setStyleSheet("color: #94A3B8;")
        
        brand_box.addLayout(logo_lay)
        brand_box.addWidget(tagline)
        layout.addLayout(brand_box)
        
        layout.addStretch()
        
        # Live System State Indicator Badge
        from ui.theme import PulseStatusBadge
        self.system_status = PulseStatusBadge(is_active=True)
        layout.addWidget(self.system_status)
        
        # User Avatar Profile
        self.avatar = QFrame()
        self.avatar.setFixedSize(36, 36)
        self.avatar.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #8B5CF6, stop:1 #06B6D4);
            border-radius: 18px;
        """)
        avatar_lay = QHBoxLayout(self.avatar)
        avatar_lay.setContentsMargins(0, 0, 0, 0)
        
        avatar_txt = QLabel("P")
        avatar_txt.setFont(get_font(10, bold=True))
        avatar_txt.setAlignment(Qt.AlignCenter)
        avatar_txt.setStyleSheet("color: white; border: none; background: transparent;")
        avatar_lay.addWidget(avatar_txt)
        
        layout.addWidget(self.avatar)


# --- GRAND HERO CENTRAL INTERACTION SPOTLIGHT ---

class HeroInteractionCard(QFrame):
    """
    Human-centered central AI Interaction Spotlight.
    Features a giant glowing gesture orb surrounded by dynamic feedback elements,
    showing live detected gesture, active system action, and AI understanding status.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1A2234, stop:1 #111726);
                border-radius: 20px;
                border: 1px solid #2D3956;
            }}
        """)
        
        # Soft Drop Shadow
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(30)
        self.shadow.setColor(QColor(139, 92, 246, 35))
        self.shadow.setOffset(0, 6)
        self.setGraphicsEffect(self.shadow)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)
        
        # Top Live Pulse Badge
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        
        self.pulse_tag = QLabel("🟢 AI UNDERSTANDING MODE ON")
        self.pulse_tag.setFont(get_font(8, bold=True))
        self.pulse_tag.setStyleSheet("""
            background: rgba(16, 185, 129, 0.15);
            color: #34D399;
            border: 1px solid rgba(16, 185, 129, 0.35);
            border-radius: 12px;
            padding: 4px 14px;
            letter-spacing: 0.8px;
        """)
        top_bar.addWidget(self.pulse_tag)
        top_bar.addStretch()
        layout.addLayout(top_bar)
        
        # Central Spotlight Orb Container
        self.orb_frame = QFrame()
        self.orb_frame.setFixedSize(120, 120)
        self.orb_frame.setStyleSheet("""
            QFrame {
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, stop:0 #8B5CF6, stop:0.8 #4C1D95, stop:1 #1E1B4B);
                border-radius: 60px;
                border: 3px solid #A78BFA;
            }
        """)
        orb_lay = QVBoxLayout(self.orb_frame)
        orb_lay.setContentsMargins(0, 0, 0, 0)
        
        self.hero_emoji = QLabel("✋")
        self.hero_emoji.setFont(get_font(48))
        self.hero_emoji.setAlignment(Qt.AlignCenter)
        self.hero_emoji.setStyleSheet("background: transparent; border: none;")
        orb_lay.addWidget(self.hero_emoji)
        
        # Center align the orb in layout
        orb_center_lay = QHBoxLayout()
        orb_center_lay.addStretch()
        orb_center_lay.addWidget(self.orb_frame)
        orb_center_lay.addStretch()
        layout.addLayout(orb_center_lay)
        
        # Detected Gesture Text Info
        self.label_detected_prefix = QLabel("DETECTED GESTURE")
        self.label_detected_prefix.setFont(get_font(8, bold=True))
        self.label_detected_prefix.setStyleSheet("color: #A78BFA; letter-spacing: 1px;")
        self.label_detected_prefix.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_detected_prefix)
        
        self.label_gesture_name = QLabel("Open Palm")
        self.label_gesture_name.setFont(get_font(22, bold=True))
        self.label_gesture_name.setStyleSheet("color: #FFFFFF;")
        self.label_gesture_name.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_gesture_name)
        
        # Action Line
        self.action_container = QHBoxLayout()
        self.action_container.addStretch()
        
        self.action_icon = QLabel("⚡")
        self.action_icon.setFont(get_font(11))
        
        self.label_action_text = QLabel("Current Action: Launching Google Chrome")
        self.label_action_text.setFont(get_font(12, bold=True))
        self.label_action_text.setStyleSheet("color: #06B6D4;")
        
        self.action_container.addWidget(self.action_icon)
        self.action_container.addWidget(self.label_action_text)
        self.action_container.addStretch()
        layout.addLayout(self.action_container)
        
        # System Response & Confidence Row
        footer_lay = QHBoxLayout()
        footer_lay.setSpacing(20)
        footer_lay.addStretch()
        
        self.status_pill = QLabel("🟢 System Activated & Listening")
        self.status_pill.setFont(get_font(9, bold=True))
        self.status_pill.setStyleSheet("""
            background: rgba(16, 185, 129, 0.2);
            color: #34D399;
            border-radius: 8px;
            padding: 4px 12px;
        """)
        
        self.conf_pill = QLabel("Confidence: 98.6%")
        self.conf_pill.setFont(get_font(9, bold=True))
        self.conf_pill.setStyleSheet("""
            background: rgba(139, 92, 246, 0.2);
            color: #C084FC;
            border-radius: 8px;
            padding: 4px 12px;
        """)
        
        footer_lay.addWidget(self.status_pill)
        footer_lay.addWidget(self.conf_pill)
        footer_lay.addStretch()
        layout.addLayout(footer_lay)
        
    def update_interaction(self, gesture_name, action_name, status_text="Action completed successfully", confidence=98.5):
        """
        Dynamically updates the central hero display when a gesture is recognized.
        """
        # Parse emoji icon if present
        icon = "✋"
        name = gesture_name
        if "Open Palm" in gesture_name or "✋" in gesture_name:
            icon = "✋"
            name = "Open Palm"
        elif "Fist" in gesture_name or "✊" in gesture_name:
            icon = "✊"
            name = "Fist"
        elif "Peace" in gesture_name or "✌️" in gesture_name:
            icon = "✌️"
            name = "Peace Sign"
        elif "Thumbs Up" in gesture_name or "👍" in gesture_name:
            icon = "👍"
            name = "Thumbs Up"
        elif "OK" in gesture_name or "👌" in gesture_name:
            icon = "👌"
            name = "OK Gesture"
        elif "Pinch" in gesture_name or "🤏" in gesture_name:
            icon = "🤏"
            name = "Pinch Gesture"
            
        self.hero_emoji.setText(icon)
        self.label_gesture_name.setText(name)
        self.label_action_text.setText(f"Current Action: {action_name}")
        self.status_pill.setText(f"🟢 {status_text}")
        self.conf_pill.setText(f"Confidence: {confidence:.1f}%")
        
        # Trigger pulse border highlight
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #232D44, stop:1 #131A2B);
                border-radius: 20px;
                border: 2px solid #06B6D4;
            }}
        """)


# --- GESTURE SHOWCASE GALLERY CARD ---

class GestureGalleryCard(QFrame):
    """
    Card displaying a single gesture showcase item for recruiters and users.
    """
    def __init__(self, icon, name, action, status="MAPPED", is_primary=False, parent=None):
        super().__init__(parent)
        t = get_theme()
        
        border_col = ACCENT if is_primary else BORDER_COLOR
        bg_col = "#1B2236" if is_primary else BG_CARD
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_col};
                border-radius: 14px;
                border: 1px solid {border_col};
            }}
            QFrame:hover {{
                border-color: #06B6D4;
                background-color: #20273D;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        
        # Header Row
        head_lay = QHBoxLayout()
        
        icon_lbl = QLabel(icon)
        icon_lbl.setFont(get_font(18))
        
        badge = QLabel(status)
        badge.setFont(get_font(7, bold=True))
        if status == "ACTIVE":
            badge.setStyleSheet("background: rgba(16, 185, 129, 0.2); color: #34D399; border-radius: 4px; padding: 2px 6px;")
        elif status == "STANDBY":
            badge.setStyleSheet("background: rgba(245, 158, 11, 0.2); color: #FBBF24; border-radius: 4px; padding: 2px 6px;")
        else:
            badge.setStyleSheet(f"background: rgba(124, 58, 237, 0.2); color: {ACCENT_HOVER}; border-radius: 4px; padding: 2px 6px;")
            
        head_lay.addWidget(icon_lbl)
        head_lay.addStretch()
        head_lay.addWidget(badge)
        layout.addLayout(head_lay)
        
        # Name
        name_lbl = QLabel(name)
        name_lbl.setFont(get_font(11, bold=True))
        name_lbl.setStyleSheet("color: #F8FAFC;")
        layout.addWidget(name_lbl)
        
        # Action Arrow mapping
        action_lay = QHBoxLayout()
        action_lay.setSpacing(6)
        
        arrow = QLabel("→")
        arrow.setFont(get_font(10, bold=True))
        arrow.setStyleSheet(f"color: {ACCENT};")
        
        action_lbl = QLabel(action)
        action_lbl.setFont(get_font(9))
        action_lbl.setStyleSheet("color: #06B6D4;")
        action_lbl.setWordWrap(True)
        
        action_lay.addWidget(arrow)
        action_lay.addWidget(action_lbl, 1)
        layout.addLayout(action_lay)


# --- PRODUCT ACTIVITY FEED TIMELINE ---

class ProductActivityFeed(QFrame):
    """
    Clean product activity timeline feed replacing plain developer logs.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border-radius: 14px;
                border: 1px solid {BORDER_COLOR};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        
        header = QHBoxLayout()
        title = QLabel("PRODUCT ACTIVITY FEED")
        title.setFont(get_font(8, bold=True))
        title.setStyleSheet("color: #818CF8; letter-spacing: 1px;")
        
        subtitle = QLabel("Real-time timeline")
        subtitle.setFont(get_font(8))
        subtitle.setStyleSheet(f"color: {TEXT_MUTED};")
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(subtitle)
        layout.addLayout(header)
        
        # Activity List
        self.feed_layout = QVBoxLayout()
        self.feed_layout.setSpacing(8)
        
        items = [
            ("10:42:18", "👍 Thumbs Up detected", "Coding Flow executed successfully", "SUCCESS"),
            ("10:42:16", "✌️ Peace Sign detected", "Chrome web browser launched", "SUCCESS"),
            ("10:42:15", "✋ Open Palm detected", "LensFlow AI tracking activated", "ACTIVE"),
        ]
        
        for time_str, event, result, status in items:
            row = QFrame()
            row.setStyleSheet("background: #111625; border-radius: 8px; border: 1px solid #1E2640;")
            r_lay = QHBoxLayout(row)
            r_lay.setContentsMargins(12, 8, 12, 8)
            r_lay.setSpacing(12)
            
            t_lbl = QLabel(time_str)
            t_lbl.setFont(get_font(8, bold=True))
            t_lbl.setStyleSheet("color: #818CF8;")
            t_lbl.setFixedWidth(65)
            
            e_lbl = QLabel(event)
            e_lbl.setFont(get_font(9, bold=True))
            e_lbl.setStyleSheet("color: #F8FAFC;")
            
            res_lbl = QLabel(result)
            res_lbl.setFont(get_font(8))
            res_lbl.setStyleSheet(f"color: {TEXT_MUTED};")
            
            st_badge = QLabel("Completed")
            st_badge.setFont(get_font(7, bold=True))
            st_badge.setStyleSheet("background: rgba(16, 185, 129, 0.2); color: #34D399; border-radius: 4px; padding: 2px 6px;")
            
            r_lay.addWidget(t_lbl)
            r_lay.addWidget(e_lbl)
            r_lay.addWidget(res_lbl, 1)
            r_lay.addWidget(st_badge)
            
            self.feed_layout.addWidget(row)
            
        layout.addLayout(self.feed_layout)


# --- PAGES ---

class DashboardHome(QWidget):
    workspace_changed = Signal(str)  # Emits Studio name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.studio_manager = StudioManager()
        self.flow_manager = FlowManager()
        self.current_studio = None
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Embed minimal Top Bar
        self.top_bar = TopBar()
        self.layout.addWidget(self.top_bar)
        
        # Workspace content area wrapped in scroll area for full responsiveness
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 20, 30, 30)
        content_layout.setSpacing(24)
        
        # 1. Greeting Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        
        now = datetime.datetime.now()
        if now.hour < 12:
            greet_text = "Good Morning, Praveena 👋"
        elif now.hour < 17:
            greet_text = "Good Afternoon, Praveena 👋"
        else:
            greet_text = "Good Evening, Praveena 👋"
            
        self.greeting = QLabel(greet_text)
        self.greeting.setFont(get_font(20, bold=True))
        self.greeting.setStyleSheet("color: #F8FAFC;")
        
        self.subgreeting = QLabel("Welcome to LensFlow — AI-Powered Accessibility & Gesture Control Platform.")
        self.subgreeting.setFont(get_font(11))
        self.subgreeting.setStyleSheet("color: #818CF8;")
        
        header_layout.addWidget(self.greeting)
        header_layout.addWidget(self.subgreeting)
        content_layout.addLayout(header_layout)
        
        # 2. Main Hero Interaction Area
        self.hero_deck = HeroInteractionCard()
        content_layout.addWidget(self.hero_deck)
        
        # 3. Gesture Showcase Row (4 Quick Showcase Cards)
        g_showcase_header = QLabel("GESTURE CONTROL SHOWCASE")
        g_showcase_header.setFont(get_font(8, bold=True))
        g_showcase_header.setStyleSheet("color: #818CF8; letter-spacing: 1px;")
        content_layout.addWidget(g_showcase_header)
        
        showcase_lay = QHBoxLayout()
        showcase_lay.setSpacing(14)
        
        cards_data = [
            ("✋", "Open Palm", "Activate Tracking System", "ACTIVE", True),
            ("✊", "Fist", "Deactivate / Standby Mode", "STANDBY", False),
            ("✌️", "Peace Sign", "Launch Chrome Web Browser", "MAPPED", False),
            ("👍", "Thumbs Up", "Run Developer Automation", "MAPPED", False),
        ]
        
        for icon, name, action, status, is_prim in cards_data:
            c_widget = GestureGalleryCard(icon, name, action, status=status, is_primary=is_prim)
            showcase_lay.addWidget(c_widget, 1)
            
        content_layout.addLayout(showcase_lay)
        
        # 4. Workspace Studios Grid Header
        studios_header = QLabel("WORKSPACES & STUDIOS")
        studios_header.setFont(get_font(8, bold=True))
        studios_header.setStyleSheet("color: #818CF8; letter-spacing: 1px;")
        content_layout.addWidget(studios_header)
        
        # Responsive 3-Column Grid of Studio Cards
        self.grid = QGridLayout()
        self.grid.setSpacing(16)
        self.load_studios()
        content_layout.addLayout(self.grid)
        
        scroll_area.setWidget(content_widget)
        self.layout.addWidget(scroll_area, 1)


    def load_studios(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.studios = self.studio_manager.get_studios()
        for idx, studio in enumerate(self.studios):
            name = studio["name"]
            icon = studio["icon"]
            desc = studio["description"]
            apps = self.flow_manager.get_apps_for_flow(studio["flow"])
            last = studio["last_used"]

            card = StudioCard(
                name=name,
                icon=icon,
                desc=desc,
                apps=apps,
                last_used=last
            )

            card.clicked.connect(self.on_studio_click)
            card.settings_clicked.connect(self.on_studio_settings)

            row = idx // 3
            col = idx % 3
            self.grid.addWidget(card, row, col)
        # Add primary Create Studio card at the end
        self.btn_create_studio = StudioCard(
            name="Create Studio",
            icon="➕",
            desc="Design a new workspace custom tailored to your routines.",
            apps=[],
            is_create_card=True
        )
        self.btn_create_studio.clicked.connect(self.on_studio_click)
        self.grid.addWidget(self.btn_create_studio, 1, 2)
    
    def on_studio_click(self, name):

        # Keep the existing signal
        self.workspace_changed.emit(name)

        # Ignore the create button for now
        if name == "CreateStudio":
            dialog = CreateStudioDialog(self)
            if dialog.exec():
                self.studio_manager.add_studio(
                    dialog.name,
                    dialog.description,
                    dialog.icon
                )
                self.load_studios()
            return

        # Look up the studio
        studio = self.studio_manager.get_studio(name.lower())
        from ui.theme_manager import set_theme
        set_theme(
            studio.get("theme", "midnight")
        )
        print(studio["theme"])

        if not studio:
            print(f"Studio not found: {name}")
            return

        print(f"Selected {studio['name']} Studio")
        self.current_studio = studio
        self.flow_manager.set_current_studio(studio)

    def on_studio_settings(self, name):
        studio = self.studio_manager.get_studio(name.lower())
        if not studio:
            print("Studio not found")
            return
        dialog = StudioSettingsDialog(studio, self)
        if dialog.exec():
            self.studios = self.studio_manager.get_studios()
            self.load_studios()
    


class FlowsPage(QWidget):
    """
    The hero feature - visual flow pipeline configurations
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(20)
        
        # Left side: existing flows list
        left_panel = QVBoxLayout()
        left_panel.setSpacing(12)
        
        title = QLabel("⚡ Flows")
        title.setFont(get_font(18, bold=True))
        left_panel.addWidget(title)
        
        flows_scroll = QScrollArea()
        flows_scroll.setWidgetResizable(True)
        flows_scroll.setStyleSheet("background: transparent; border: none;")
        
        flows_list_widget = QWidget()
        flows_list_layout = QVBoxLayout(flows_list_widget)
        flows_list_layout.setSpacing(10)
        flows_list_layout.setContentsMargins(0, 0, 0, 0)
        
        flow_data = [
            ("Coding Flow", "Launched by Thumbs Up", True),
            ("Presentation Setup", "Launched by Peace Sign", False),
            ("Gaming Mode", "Launched by OK Gesture", False),
            ("Media Controller", "Launched by Index Finger", False),
        ]
        
        for name, desc, active in flow_data:
            card = HoverCard()
            card_lay = QVBoxLayout(card)
            card_lay.setContentsMargins(15, 12, 15, 12)
            card_lay.setSpacing(4)
            
            c_header = QHBoxLayout()
            c_title = QLabel(name)
            c_title.setFont(get_font(10, bold=True))
            c_header.addWidget(c_title)
            
            if active:
                badge = QLabel("Active")
                badge.setFont(get_font(8, bold=True))
                badge.setStyleSheet(f"background-color: {SUCCESS}; color: white; border-radius: 4px; padding: 2px 6px;")
                c_header.addWidget(badge, 0, Qt.AlignRight)
                
            c_desc = QLabel(desc)
            c_desc.setFont(get_font(9))
            c_desc.setStyleSheet(f"color: {TEXT_MUTED};")
            
            card_lay.addLayout(c_header)
            card_lay.addWidget(c_desc)
            flows_list_layout.addWidget(card)
            
        flows_list_layout.addStretch()
        flows_scroll.setWidget(flows_list_widget)
        left_panel.addWidget(flows_scroll, 1)
        
        # Right side: flow designer
        right_panel = QVBoxLayout()
        right_panel.setSpacing(12)
        
        editor_title = QLabel("FLOW DESIGNER")
        editor_title.setFont(get_font(8, bold=True))
        editor_title.setStyleSheet(f"color: {TEXT_MUTED};")
        right_panel.addWidget(editor_title)
        
        editor_card = QFrame()
        editor_card.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border-radius: 12px;
                border: 1px solid {BORDER_COLOR};
            }}
        """)
        ed_layout = QVBoxLayout(editor_card)
        ed_layout.setContentsMargins(20, 20, 20, 20)
        ed_layout.setSpacing(16)
        
        fd_header = QHBoxLayout()
        fd_title = QLabel("Coding Flow")
        fd_title.setFont(get_font(14, bold=True))
        fd_header.addWidget(fd_title)
        
        btn_run = ModernButton("Run Test", primary=True)
        btn_run.setFixedHeight(30)
        fd_header.addWidget(btn_run, 0, Qt.AlignRight)
        ed_layout.addLayout(fd_header)
        
        steps_lay = QVBoxLayout()
        steps_lay.setSpacing(12)
        
        steps = [
            ("1. Launch Application", "Target: Chrome (C:\\Program Files...)", "🚀"),
            ("2. Delay Wait Timer", "Duration: 2.0 seconds", "⏳"),
            ("3. Navigate URL Webpage", "URL: https://github.com", "🌐")
        ]
        
        for s_title, s_desc, s_icon in steps:
            s_widget = QFrame()
            s_widget.setStyleSheet(f"background-color: #1F2937; border-radius: 8px; border: 1px solid {BORDER_COLOR};")
            s_w_lay = QHBoxLayout(s_widget)
            s_w_lay.setContentsMargins(12, 10, 12, 10)
            
            icon = QLabel(s_icon)
            icon.setFont(get_font(12))
            
            lbl_lay = QVBoxLayout()
            lbl_lay.setSpacing(2)
            st_lbl = QLabel(s_title)
            st_lbl.setFont(get_font(9, bold=True))
            st_lbl.setStyleSheet("color: white;")
            sd_lbl = QLabel(s_desc)
            sd_lbl.setFont(get_font(8))
            sd_lbl.setStyleSheet(f"color: {TEXT_MUTED};")
            lbl_lay.addWidget(st_lbl)
            lbl_lay.addWidget(sd_lbl)
            
            s_w_lay.addWidget(icon)
            s_w_lay.addLayout(lbl_lay, 1)
            
            steps_lay.addWidget(s_widget)
            
        ed_layout.addLayout(steps_lay)
        ed_layout.addStretch()
        
        btn_add_step = ModernButton("+ Add Automation Action")
        ed_layout.addWidget(btn_add_step)
        
        right_panel.addWidget(editor_card, 1)
        
        layout.addLayout(left_panel, 2)
        layout.addLayout(right_panel, 3)


class WorkspacesPage(QWidget):
    """
    Profiles configurator list.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(16)
        
        title = QLabel("👤 Profiles Configurator")
        title.setFont(get_font(18, bold=True))
        layout.addWidget(title)
        
        grid = QGridLayout()
        grid.setSpacing(16)
        
        workspaces = [
            ("Coding Setup", "Customized for VS Code automation, Google Search, and GitHub integrations. Active when coding.", True),
            ("Gaming Setup", "Mapped to Discord, Steam launching, and recording controls. Low recognition delay active.", False),
            ("Creative Canvas", "Optimized gestures for PowerPoint, PDF navigation, and laser pointer toggles.", False),
            ("Presentation Mode", "Universal gesture profile mapping hand speed to system volume and media triggers.", False)
        ]
        
        for idx, (p_name, p_desc, active) in enumerate(workspaces):
            card = HoverCard()
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(20, 20, 20, 20)
            card_layout.setSpacing(8)
            
            h_lay = QHBoxLayout()
            lbl_name = QLabel(p_name)
            lbl_name.setFont(get_font(12, bold=True))
            h_lay.addWidget(lbl_name)
            
            if active:
                lbl_badge = QLabel("Active")
                lbl_badge.setFont(get_font(8, bold=True))
                lbl_badge.setStyleSheet(f"background-color: {SUCCESS}; color: white; border-radius: 4px; padding: 2px 6px;")
                h_lay.addWidget(lbl_badge, 0, Qt.AlignRight)
                
            lbl_desc = QLabel(p_desc)
            lbl_desc.setWordWrap(True)
            lbl_desc.setFont(get_font(9))
            lbl_desc.setStyleSheet(f"color: {TEXT_MUTED};")
            
            card_layout.addLayout(h_lay)
            card_layout.addWidget(lbl_desc)
            card_layout.addStretch()
            
            btn_activate = ModernButton("Selected Profile" if active else "Select Profile", primary=active)
            card_layout.addWidget(btn_activate)
            
            row = idx // 2
            col = idx % 2
            grid.addWidget(card, row, col)
            
        layout.addLayout(grid, 1)


class LivePage(QWidget):
    """
    Dedicated AI Telemetry Cockpit.
    Contains Camera viewfinder, AI statistics, and the pipeline timeline.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(24)
        
        # Left Panel: Control Deck
        left_layout = QVBoxLayout()
        left_layout.setSpacing(16)
        
        title = QLabel("✋ Live AI Cockpit")
        title.setFont(get_font(18, bold=True))
        left_layout.addWidget(title)
        
        # Deploy specs card
        specs_card = QFrame()
        specs_card.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_COLOR};
                border-radius: 12px;
            }}
        """)
        specs_lay = QVBoxLayout(specs_card)
        specs_lay.setContentsMargins(15, 15, 15, 15)
        specs_lay.setSpacing(10)
        
        specs_lbl = QLabel("TRACKING ENGINE SPECIFICATIONS")
        specs_lbl.setFont(get_font(8, bold=True))
        specs_lbl.setStyleSheet(f"color: {TEXT_MUTED}; letter-spacing: 0.5px;")
        specs_lay.addWidget(specs_lbl)
        
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("MediaPipe Engine:"))
        lbl_v = QLabel("v2.4 (Local Pipeline)")
        lbl_v.setFont(get_font(9, bold=True))
        row1.addWidget(lbl_v, 0, Qt.AlignRight)
        specs_lay.addLayout(row1)
        
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Accelerator Platform:"))
        lbl_acc = QLabel("Local CPU (Intel OpenVINO)")
        lbl_acc.setFont(get_font(9, bold=True))
        row2.addWidget(lbl_acc, 0, Qt.AlignRight)
        specs_lay.addLayout(row2)
        
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Engine Frame Rate:"))
        lbl_fps = QLabel("30.4 FPS")
        lbl_fps.setFont(get_font(9, bold=True))
        lbl_fps.setStyleSheet(f"color: {SUCCESS};")
        row3.addWidget(lbl_fps, 0, Qt.AlignRight)
        specs_lay.addLayout(row3)
        
        left_layout.addWidget(specs_card)
        
        # Active Gestures Mappings inside the Cockpit
        gestures_card = QFrame()
        gestures_card.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_COLOR};
                border-radius: 12px;
            }}
        """)
        gestures_lay = QVBoxLayout(gestures_card)
        gestures_lay.setContentsMargins(15, 15, 15, 15)
        gestures_lay.setSpacing(8)
        
        g_lbl = QLabel("ACTIVE GESTURE MAPS")
        g_lbl.setFont(get_font(8, bold=True))
        g_lbl.setStyleSheet("color: #818CF8; letter-spacing: 0.5px;")
        gestures_lay.addWidget(g_lbl)
        
        gestures_lay.addWidget(QLabel("✋ Open Palm  →  Activate System Tracking (Status: ACTIVE)"))
        gestures_lay.addWidget(QLabel("✊ Fist       →  Deactivate System Control (Status: STANDBY)"))
        gestures_lay.addWidget(QLabel("👍 Thumbs Up  →  Launch Chrome & Developer Tools"))
        gestures_lay.addWidget(QLabel("✌️ Peace Sign →  Navigate to Web Dashboard"))
        
        left_layout.addWidget(gestures_card)
        
        # Product Activity Feed Timeline
        self.activity_feed = ProductActivityFeed()
        left_layout.addWidget(self.activity_feed)
        
        self.btn_toggle = ModernButton("Start Live Camera Pipeline", gradient=True)
        left_layout.addWidget(self.btn_toggle)
        self.btn_toggle.clicked.connect(self.start_camera)

        # Right Panel: Telemetry module
        self.right_panel = RightPanel()

        # Camera thread
        self.camera = CameraThread()
        self.camera.frame_ready.connect(
            self.right_panel.camera_view.update_frame
        )

        # Give right panel curved borders to match the design
        self.right_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_COLOR};
                border-radius: 14px;
            }}
        """)
        
        layout.addLayout(left_layout, 3)
        layout.addWidget(self.right_panel, 2)
    
    def start_camera(self):
        if not self.camera.isRunning():
            self.camera.start()


class GesturesPage(QWidget):
    """
    Visually appealing Gesture Showcase Gallery for recruiters and users.
    Displays clear gesture-to-action mappings with status badges.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(20)
        
        # Header
        header = QVBoxLayout()
        header.setSpacing(4)
        
        title = QLabel("✋ Gesture Showcase Gallery")
        title.setFont(get_font(20, bold=True))
        title.setStyleSheet("color: #F8FAFC;")
        
        subtitle = QLabel("Visual demonstration of LensFlow hand tracking triggers and assigned actions.")
        subtitle.setFont(get_font(11))
        subtitle.setStyleSheet("color: #818CF8;")
        
        header.addWidget(title)
        header.addWidget(subtitle)
        layout.addLayout(header)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        scroll_content = QWidget()
        scroll_layout = QGridLayout(scroll_content)
        scroll_layout.setSpacing(16)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        gestures = [
            ("✋", "Open Palm", "Activate System Tracking & Listening", "ACTIVE", "Wakes up AI pipeline and listens for incoming commands."),
            ("✊", "Fist", "Deactivate System & Enter Standby", "STANDBY", "Pauses computer control for privacy & safety."),
            ("✌️", "Peace Sign", "Launch Chrome Web Browser", "MAPPED", "Triggers web browser launch with quick URLs."),
            ("👍", "Thumbs Up", "Execute Productivity Automation", "MAPPED", "Launches VS Code, Terminal & GitHub tabs."),
            ("👌", "OK Gesture", "Open Spotify & Control Media", "READY", "Starts background music playback and media keys."),
            ("🤏", "Pinch", "Perform Left Mouse Click", "READY", "Precise touchless cursor interaction mode."),
            ("☝️", "Index Finger", "Toggle Precise Cursor Scroll", "READY", "Smooth scroll control across long web pages.")
        ]
        
        for idx, (icon, name, action, status, desc) in enumerate(gestures):
            card = QFrame()
            is_active = (status == "ACTIVE")
            border_col = "#7C3AED" if is_active else "#262E48"
            bg_col = "#1B2236" if is_active else BG_CARD
            
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {bg_col};
                    border: 1px solid {border_col};
                    border-radius: 14px;
                }}
                QFrame:hover {{
                    border-color: #06B6D4;
                    background-color: #20273D;
                }}
            """)
            
            c_lay = QVBoxLayout(card)
            c_lay.setContentsMargins(18, 16, 18, 16)
            c_lay.setSpacing(10)
            
            # Row 1: Icon & Status Pill
            top_lay = QHBoxLayout()
            icon_lbl = QLabel(icon)
            icon_lbl.setFont(get_font(22))
            
            badge = QLabel(status)
            badge.setFont(get_font(7, bold=True))
            if status == "ACTIVE":
                badge.setStyleSheet("background: rgba(16, 185, 129, 0.2); color: #34D399; border-radius: 4px; padding: 3px 8px;")
            elif status == "STANDBY":
                badge.setStyleSheet("background: rgba(245, 158, 11, 0.2); color: #FBBF24; border-radius: 4px; padding: 3px 8px;")
            else:
                badge.setStyleSheet(f"background: rgba(124, 58, 237, 0.2); color: #A78BFA; border-radius: 4px; padding: 3px 8px;")
                
            top_lay.addWidget(icon_lbl)
            top_lay.addStretch()
            top_lay.addWidget(badge)
            c_lay.addLayout(top_lay)
            
            # Gesture Title
            g_title = QLabel(name)
            g_title.setFont(get_font(12, bold=True))
            g_title.setStyleSheet("color: #F8FAFC;")
            c_lay.addWidget(g_title)
            
            # Action Mapping
            act_lay = QHBoxLayout()
            act_lay.setSpacing(6)
            arr = QLabel("→")
            arr.setFont(get_font(10, bold=True))
            arr.setStyleSheet("color: #8B5CF6;")
            act_lbl = QLabel(action)
            act_lbl.setFont(get_font(10, bold=True))
            act_lbl.setStyleSheet("color: #06B6D4;")
            act_lay.addWidget(arr)
            act_lay.addWidget(act_lbl, 1)
            c_lay.addLayout(act_lay)
            
            # Description
            d_lbl = QLabel(desc)
            d_lbl.setFont(get_font(8))
            d_lbl.setStyleSheet("color: #818CF8;")
            d_lbl.setWordWrap(True)
            c_lay.addWidget(d_lbl)
            
            row = idx // 2
            col = idx % 2
            scroll_layout.addWidget(card, row, col)
            
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)


class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(20)
        
        title = QLabel("⚙ Settings")
        title.setFont(get_font(18, bold=True))
        layout.addWidget(title)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(20)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        # Camera Settings
        grp_camera = QFrame()
        grp_camera.setStyleSheet(f"background-color: {BG_CARD}; border: 1px solid {BORDER_COLOR}; border-radius: 12px;")
        gc_lay = QVBoxLayout(grp_camera)
        gc_lay.setContentsMargins(20, 20, 20, 20)
        gc_lay.setSpacing(12)
        
        gc_title = QLabel("CAMERA SETTINGS")
        gc_title.setFont(get_font(8, bold=True))
        gc_title.setStyleSheet(f"color: {TEXT_MUTED};")
        gc_lay.addWidget(gc_title)
        
        camera_row = QHBoxLayout()
        cam_lbl = QLabel("Camera Input Source:")
        cam_lbl.setFont(get_font(10))
        cam_combo = QComboBox()
        cam_combo.addItems(["Default Webcam (Index 0)", "USB Camera (Index 1)", "OBS Virtual Camera (Index 2)"])
        cam_combo.setMinimumWidth(200)
        cam_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: #18181B;
                border: 1px solid {BORDER_COLOR};
                border-radius: 6px;
                padding: 6px 12px;
                color: white;
            }}
        """)
        camera_row.addWidget(cam_lbl)
        camera_row.addWidget(cam_combo, 0, Qt.AlignRight)
        gc_lay.addLayout(camera_row)
        
        scroll_layout.addWidget(grp_camera)
        
        # Detection Parameters
        grp_detect = QFrame()
        grp_detect.setStyleSheet(f"background-color: {BG_CARD}; border: 1px solid {BORDER_COLOR}; border-radius: 12px;")
        gd_lay = QVBoxLayout(grp_detect)
        gd_lay.setContentsMargins(20, 20, 20, 20)
        gd_lay.setSpacing(15)
        
        gd_title = QLabel("DETECTION PARAMETERS")
        gd_title.setFont(get_font(8, bold=True))
        gd_title.setStyleSheet(f"color: {TEXT_MUTED};")
        gd_lay.addWidget(gd_title)
        
        hand_row = QHBoxLayout()
        hand_lbl = QLabel("Max Hands to Track:")
        hand_lbl.setFont(get_font(10))
        hand_val = QLabel("2")
        hand_val.setFont(get_font(10, bold=True))
        hand_val.setStyleSheet(f"color: {ACCENT};")
        hand_row.addWidget(hand_lbl)
        hand_row.addWidget(hand_val, 0, Qt.AlignRight)
        gd_lay.addLayout(hand_row)
        
        conf_row = QHBoxLayout()
        conf_lbl = QLabel("Minimum Confidence Threshold:")
        conf_lbl.setFont(get_font(10))
        conf_val = QLabel("0.70")
        conf_val.setFont(get_font(10, bold=True))
        conf_val.setStyleSheet(f"color: {ACCENT};")
        conf_row.addWidget(conf_lbl)
        conf_row.addWidget(conf_val, 0, Qt.AlignRight)
        gd_lay.addLayout(conf_row)
        
        slider_conf = QSlider(Qt.Horizontal)
        slider_conf.setRange(50, 95)
        slider_conf.setValue(70)
        slider_conf.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: 1px solid {BORDER_COLOR};
                height: 6px;
                background: #18181B;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {ACCENT};
                width: 14px;
                margin-top: -4px;
                margin-bottom: -4px;
                border-radius: 7px;
            }}
        """)
        slider_conf.valueChanged.connect(lambda v: conf_val.setText(f"{v/100:.2f}"))
        gd_lay.addWidget(slider_conf)
        
        scroll_layout.addWidget(grp_detect)
        
        # Developer Keys
        grp_profile = QFrame()
        grp_profile.setStyleSheet(f"background-color: {BG_CARD}; border: 1px solid {BORDER_COLOR}; border-radius: 12px;")
        gp_lay = QVBoxLayout(grp_profile)
        gp_lay.setContentsMargins(20, 20, 20, 20)
        gp_lay.setSpacing(12)
        
        gp_title = QLabel("DEVELOPER CONSOLE SETTINGS")
        gp_title.setFont(get_font(8, bold=True))
        gp_title.setStyleSheet(f"color: {TEXT_MUTED};")
        gp_lay.addWidget(gp_title)
        
        dev_row = QHBoxLayout()
        dev_lbl = QLabel("Dev Server Port:")
        dev_lbl.setFont(get_font(10))
        dev_input = QLineEdit("8080")
        dev_input.setFixedWidth(100)
        dev_input.setStyleSheet(f"background: #18181B; border: 1px solid {BORDER_COLOR}; border-radius: 6px; padding: 4px; color: white;")
        dev_row.addWidget(dev_lbl)
        dev_row.addWidget(dev_input, 0, Qt.AlignRight)
        gp_lay.addLayout(dev_row)
        
        scroll_layout.addWidget(grp_profile)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)
        
        btn_save = ModernButton("Save Changes", primary=True)
        btn_save.setFixedWidth(200)
        layout.addWidget(btn_save, 0, Qt.AlignRight)

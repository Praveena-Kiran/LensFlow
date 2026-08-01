from PySide6.QtGui import QPixmap
from mediapipe.tasks.cc.vision.gesture_recognizer.proto import gesture_classifier_graph_options_pb2
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QWidget
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QPen
from ui.theme import (
    BG_CARD, BORDER_COLOR, ACCENT, SUCCESS, TEXT_PRIMARY, TEXT_MUTED, get_font
)
from PySide6.QtGui import QImage, QPixmap
import cv2

class CameraViewfinder(QFrame):
    """
    A stylized futuristic viewfinder simulating a camera input.
    Draws a camera grid and a blinking status indicator.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(180)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1F2937, stop:1 #111827);
                border-radius: 12px;
                border: 1px dashed {BORDER_COLOR};
            }}
        """)
        
        # Center message
        self.layout = QVBoxLayout(self)
        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setScaledContents(True)
        self.layout.addWidget(self.camera_label)
        
        # Blink animation timer for "OFFLINE" badge
        self.badge_visible = True
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.toggle_badge)
        self.timer.start(1000)
        
    def toggle_badge(self):
        self.badge_visible = not self.badge_visible
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw viewfinder corners in bright Cyan/Violet
        w, h = self.width(), self.height()
        pen = QPen(QColor("#06B6D4"), 2)
        painter.setPen(pen)
        
        length = 18
        
        # Top-Left
        painter.drawLine(12, 12, 12 + length, 12)
        painter.drawLine(12, 12, 12, 12 + length)
        
        # Top-Right
        painter.drawLine(w - 12, 12, w - 12 - length, 12)
        painter.drawLine(w - 12, 12, w - 12, 12 + length)
        
        # Bottom-Left
        painter.drawLine(12, h - 12, 12 + length, h - 12)
        painter.drawLine(12, h - 12, 12, h - 12 - length)
        
        # Bottom-Right
        painter.drawLine(w - 12, h - 12, w - 12 - length, h - 12)
        painter.drawLine(w - 12, h - 12, w - 12, h - 12 - length)
        
        # HUD Status Badge
        if self.badge_visible:
            painter.setBrush(QColor("#10B981"))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(w - 28, 18, 8, 8)
            
            painter.setPen(QColor("#34D399"))
            painter.drawText(w - 75, 26, "REC LIVE")

    def update_frame(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        image = QImage(
            rgb.data,
            w,
            h,
            bytes_per_line,
            QImage.Format_RGB888
        )
        pixmap = QPixmap.fromImage(image)
        self.camera_label.setPixmap(pixmap)


class TimelineStep(QWidget):
    """
    A single node in the automation vertical timeline.
    """
    def __init__(self, title, description, status="pending", parent=None):
        super().__init__(parent)
        self.status = status
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Indicator Dot & vertical line drawing widget
        self.indicator = QWidget()
        self.indicator.setFixedWidth(16)
        self.indicator_layout = QVBoxLayout(self.indicator)
        self.indicator_layout.setContentsMargins(0, 0, 0, 0)
        self.indicator_layout.setSpacing(0)
        
        # Top Line, Dot, Bottom Line
        self.dot = QLabel()
        self.dot.setFixedSize(10, 10)
        
        if status == "success":
            dot_color = SUCCESS
        elif status == "active":
            dot_color = ACCENT
        else:
            dot_color = "#3F3F46"
            
        self.dot.setStyleSheet(f"""
            background-color: {dot_color};
            border-radius: 5px;
        """)
        
        self.indicator_layout.addWidget(self.dot, 0, Qt.AlignCenter)
        
        # Labels layout
        labels_widget = QWidget()
        labels_layout = QVBoxLayout(labels_widget)
        labels_layout.setContentsMargins(0, 0, 0, 0)
        labels_layout.setSpacing(2)
        
        self.title_lbl = QLabel(title)
        self.title_lbl.setFont(get_font(9, bold=True))
        if status == "pending":
            self.title_lbl.setStyleSheet(f"color: {TEXT_MUTED};")
        else:
            self.title_lbl.setStyleSheet(f"color: {TEXT_PRIMARY};")
            
        self.desc_lbl = QLabel(description)
        self.desc_lbl.setFont(get_font(8))
        self.desc_lbl.setStyleSheet(f"color: {TEXT_MUTED};")
        
        labels_layout.addWidget(self.title_lbl)
        labels_layout.addWidget(self.desc_lbl)
        
        layout.addWidget(self.indicator, 0, Qt.AlignTop)
        layout.addWidget(labels_widget, 1)


class RightPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(300)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border-left: 1px solid {BORDER_COLOR};
            }}
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 24, 20, 24)
        self.layout.setSpacing(20)
        
        # Title/Header
        self.header_label = QLabel("FEED & TELEMETRY")
        self.header_label.setFont(get_font(8, bold=True))
        self.header_label.setStyleSheet(f"color: {TEXT_MUTED}; letter-spacing: 1px;")
        self.layout.addWidget(self.header_label)
        
        # Camera view container
        self.camera_view = CameraViewfinder()
        self.layout.addWidget(self.camera_view)
        
        # Metrics card
        self.metrics_card = QFrame()
        self.metrics_card.setStyleSheet(f"""
            QFrame {{
                background-color: #1F2937;
                border-radius: 12px;
                border: 1px solid {BORDER_COLOR};
            }}
        """)
        metrics_layout = QVBoxLayout(self.metrics_card)
        metrics_layout.setContentsMargins(15, 15, 15, 15)
        metrics_layout.setSpacing(12)
        
        # Title of telemetry
        tel_lbl = QLabel("GESTURE TELEMETRY")
        tel_lbl.setFont(get_font(8, bold=True))
        tel_lbl.setStyleSheet(f"color: {TEXT_MUTED};")
        metrics_layout.addWidget(tel_lbl)
        
        # Detected Gesture row
        gesture_row = QHBoxLayout()
        gesture_lbl = QLabel("Gesture:")
        gesture_lbl.setFont(get_font(9))
        gesture_lbl.setStyleSheet(f"color: {TEXT_MUTED};")
        self.detected_val = QLabel("None")
        self.detected_val.setFont(get_font(11, bold=True))
        self.detected_val.setStyleSheet("color: white;")
        gesture_row.addWidget(gesture_lbl)
        gesture_row.addWidget(self.detected_val, 0, Qt.AlignRight)
        metrics_layout.addLayout(gesture_row)
        
        # Confidence row
        conf_lbl = QLabel("Confidence:")
        conf_lbl.setFont(get_font(9))
        conf_lbl.setStyleSheet(f"color: {TEXT_MUTED};")
        metrics_layout.addWidget(conf_lbl)
        
        # Confidence progress bar
        self.conf_bar = QProgressBar()
        self.conf_bar.setValue(0)
        self.conf_bar.setFont(get_font(8, bold=True))
        self.conf_bar.setAlignment(Qt.AlignCenter)
        self.conf_bar.setFixedHeight(12)
        self.conf_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {BORDER_COLOR};
                border-radius: 6px;
                background-color: #111827;
                text-align: center;
                color: transparent;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT}, stop:1 {SUCCESS});
                border-radius: 5px;
            }}
        """)
        metrics_layout.addWidget(self.conf_bar)
        
        self.conf_percent_lbl = QLabel("0.0%")
        self.conf_percent_lbl.setFont(get_font(9, bold=True))
        self.conf_percent_lbl.setStyleSheet(f"color: {SUCCESS};")
        metrics_layout.addWidget(self.conf_percent_lbl, 0, Qt.AlignRight)
        
        self.layout.addWidget(self.metrics_card)
        
        # Automation timeline
        timeline_header = QLabel("AUTOMATION PIPELINE")
        timeline_header.setFont(get_font(8, bold=True))
        timeline_header.setStyleSheet(f"color: {TEXT_MUTED}; letter-spacing: 0.5px;")
        self.layout.addWidget(timeline_header)
        
        self.timeline_card = QFrame()
        self.timeline_card.setStyleSheet(f"""
            QFrame {{
                background-color: #111827;
                border-radius: 12px;
                border: 1px solid {BORDER_COLOR};
            }}
        """)
        self.timeline_layout = QVBoxLayout(self.timeline_card)
        self.timeline_layout.setContentsMargins(15, 15, 15, 15)
        self.timeline_layout.setSpacing(12)
        
        # Timeline items (placeholder demo of Coding Flow steps)
        self.step1 = TimelineStep("Launch Chrome", "Target: google-chrome", "success")
        self.step2 = TimelineStep("Wait 2 Seconds", "Timer delay", "active")
        self.step3 = TimelineStep("Navigate URL", "url: https://github.com", "pending")
        
        self.timeline_layout.addWidget(self.step1)
        self.timeline_layout.addWidget(self.step2)
        self.timeline_layout.addWidget(self.step3)
        self.timeline_layout.addStretch()
        
        self.layout.addWidget(self.timeline_card, 1)
        
    def set_telemetry(self, gesture, confidence):
        """
        Updates the right panel metrics dynamically (e.g., triggered by UI events or simulation)
        """
        self.detected_val.setText(gesture if gesture else "None")
        self.conf_bar.setValue(int(confidence * 100))
        self.conf_percent_lbl.setText(f"{confidence * 100:.1f}%")
        
        # Update timeline step highlights based on gesture
        if gesture == "👍 Thumbs Up":
            self.step1.status = "success"
            self.step2.status = "success"
            self.step3.status = "active"
        elif gesture == "✋ Open Palm":
            self.step1.status = "success"
            self.step2.status = "pending"
            self.step3.status = "pending"
        else:
            self.step1.status = "pending"
            self.step2.status = "pending"
            self.step3.status = "pending"
            
        # Re-update styles of steps
        # This keeps the mock working interactively
        for step in [self.step1, self.step2, self.step3]:
            dot_color = SUCCESS if step.status == "success" else (ACCENT if step.status == "active" else "#3F3F46")
            step.dot.setStyleSheet(f"background-color: {dot_color}; border-radius: 5px;")
            if step.status == "pending":
                step.title_lbl.setStyleSheet(f"color: {TEXT_MUTED};")
            else:
                step.title_lbl.setStyleSheet("color: white;")

    def set_workspace(self, name):
        """
        Dynamically shifts entire pipeline steps, confidence, and active gestures 
        based on the selected Workspace card.
        """
        # Clear existing timeline items
        while self.timeline_layout.count():
            item = self.timeline_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        # Set telemetry based on workspace selection
        if "Coding" in name:
            self.detected_val.setText("👍 Thumbs Up")
            self.conf_bar.setValue(98)
            self.conf_percent_lbl.setText("98.2%")
            
            self.step1 = TimelineStep("Launch Chrome", "Target: google-chrome", "success")
            self.step2 = TimelineStep("Wait 2 Seconds", "Timer delay", "active")
            self.step3 = TimelineStep("Navigate URL", "url: https://github.com", "pending")
            
        elif "Gaming" in name:
            self.detected_val.setText("✊ Fist")
            self.conf_bar.setValue(97)
            self.conf_percent_lbl.setText("97.5%")
            
            self.step1 = TimelineStep("Launch Steam", "Target: steam.exe", "success")
            self.step2 = TimelineStep("Launch Discord", "Target: discord.exe", "active")
            self.step3 = TimelineStep("Record Session", "Target: obs64.exe", "pending")
            
        elif "Creative" in name:
            self.detected_val.setText("🤏 Pinch")
            self.conf_bar.setValue(94)
            self.conf_percent_lbl.setText("94.1%")
            
            self.step1 = TimelineStep("Launch Figma", "Opening canvas website", "success")
            self.step2 = TimelineStep("Launch Photoshop", "Target: photoshop.exe", "active")
            self.step3 = TimelineStep("Play Chill Lo-Fi", "Spotify API trigger", "pending")
            
        elif "Presentation" in name:
            self.detected_val.setText("✌️ Peace Sign")
            self.conf_bar.setValue(96)
            self.conf_percent_lbl.setText("96.0%")
            
            self.step1 = TimelineStep("Launch PowerPoint", "Opening slideshow", "success")
            self.step2 = TimelineStep("Start Slide Show", "Press F5 shortcut", "active")
            self.step3 = TimelineStep("Enable Laser Pointer", "Hand tracking gesture", "pending")
            
        else:
            self.detected_val.setText("None")
            self.conf_bar.setValue(0)
            self.conf_percent_lbl.setText("0.0%")
            
            self.step1 = TimelineStep("No active pipeline", "Select workspace first", "pending")
            self.step2 = TimelineStep("Empty", "-", "pending")
            self.step3 = TimelineStep("Empty", "-", "pending")
            
        self.timeline_layout.addWidget(self.step1)
        self.timeline_layout.addWidget(self.step2)
        self.timeline_layout.addWidget(self.step3)
        self.timeline_layout.addStretch()

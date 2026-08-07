from PIL import ImageColor
from PySide6.QtWidgets import QLabel, QVBoxLayout, QFrame
from backend.automation.controllers.powerpoint_controller import PowerPointController
from frontend.pages.studio_page import StudioPage
from frontend.components.presentation_controls import PresentationControls

class PresentationPage(StudioPage):

    def __init__(self):
        super().__init__(
            "Presentation Studio",
            "Control PowerPoint with gestures and voice."
        )
        self.powerpoint = PowerPointController()
        self.controls = PresentationControls()
        self.content_layout.addWidget(self.controls)
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #111118;
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 14px;
            }
        """)

        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(20, 18, 20, 18)
        status_layout.setSpacing(8)

        status_title = QLabel("Presentation Status")
        status_title.setStyleSheet("""
            color: white;
            font-size: 15px;
            font-weight: 600;
        """)

        self.status = QLabel("●  Ready")
        self.status.setStyleSheet("""
            color: #34D399;
            font-size: 13px;
            font-weight: 500;
        """)

        status_detail = QLabel("PowerPoint controller ready")
        status_detail.setStyleSheet("""
            color: #6B7280;
            font-size: 12px;
        """)

        status_layout.addWidget(status_title)
        status_layout.addWidget(self.status)
        status_layout.addWidget(status_detail)

        self.content_layout.addWidget(status_frame)
        self.controls.previous_clicked.connect(
            self._previous_slide
           
        )

        self.controls.start_clicked.connect(
            self._start_presentation
            
        )  

        self.controls.next_clicked.connect(
            self._next_slide
            
        )

        self.controls.end_clicked.connect(
            self._end_presentation
            
        )

    def _set_status(self, text, color="#34D399"):
        self.status.setText(f"●  {text}")
        self.status.setStyleSheet(f"""
            color: {color};
            font-size: 13px;
            font-weight: 500;
        """)
    
    def _start_presentation(self):
        self.powerpoint.start_presentation()
        self._set_status("Presentation Running")


    def _next_slide(self):
        self.powerpoint.next_slide()
        self._set_status("Presentation Running")


    def _previous_slide(self):
        self.powerpoint.previous_slide()
        self._set_status("Presentation Running")


    def _end_presentation(self):
        self.powerpoint.end_presentation()
        self._set_status("Presentation Ended", "#9CA3AF")

    

        






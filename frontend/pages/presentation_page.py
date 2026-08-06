from PySide6.QtWidgets import QLabel, QVBoxLayout

from frontend.pages.studio_page import StudioPage


class PresentationPage(StudioPage):

    def __init__(self):
        super().__init__(
            "Presentation Studio",
            "Control PowerPoint with gestures and voice."
        )

        self.content_layout.addWidget(
            QLabel("Presentation Studio Coming Soon 🚀")
        )
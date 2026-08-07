from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
)


class PresentationControls(QFrame):

    previous_clicked = Signal()
    start_clicked = Signal()
    next_clicked = Signal()
    end_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("PresentationControls")

        self.setStyleSheet("""
            QFrame#PresentationControls {
                background-color: #16161E;
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 16px;
            }

            QLabel#SectionTitle {
                color: white;
                font-size: 16px;
                font-weight: 600;
            }

            QLabel#SectionSubtitle {
                color: #6B7280;
                font-size: 12px;
            }

            QPushButton {
                background-color: #1E1E28;
                color: #D1D5DB;
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 10px;
                font-size: 12px;
                font-weight: 600;
                padding: 10px 16px;
            }

            QPushButton:hover {
                background-color: #252532;
                border: 1px solid rgba(255, 255, 255, 0.12);
            }

            QPushButton:pressed {
                background-color: #2D2D3A;
            }

            QPushButton#StartButton {
                background-color: #3B82F6;
                color: white;
                border: none;
            }

            QPushButton#StartButton:hover {
                background-color: #60A5FA;
            }

            QPushButton#EndButton {
                color: #FCA5A5;
            }

            QPushButton#EndButton:hover {
                background-color: rgba(239, 68, 68, 0.12);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        header = QVBoxLayout()
        header.setSpacing(3)

        title = QLabel("Presentation Controls")
        title.setObjectName("SectionTitle")

        subtitle = QLabel("Control your presentation")
        subtitle.setObjectName("SectionSubtitle")

        header.addWidget(title)
        header.addWidget(subtitle)

        layout.addLayout(header)

        # Buttons
        controls = QHBoxLayout()
        controls.setSpacing(10)

        previous = QPushButton("←  Previous")
        previous.clicked.connect(self.previous_clicked.emit)

        start = QPushButton("▶  Start Presentation")
        start.setObjectName("StartButton")
        start.clicked.connect(self.start_clicked.emit)

        next_btn = QPushButton("Next  →")
        next_btn.clicked.connect(self.next_clicked.emit)

        end = QPushButton("■  End")
        end.setObjectName("EndButton")
        end.clicked.connect(self.end_clicked.emit)

        controls.addWidget(previous)
        controls.addWidget(start, 1)
        controls.addWidget(next_btn)
        controls.addWidget(end)

        layout.addLayout(controls)
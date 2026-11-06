from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
)
from frontend.styles.theme import (
    SURFACE,
    BORDER,
    PRIMARY,
    PRIMARY_HOVER,
    PRIMARY_PRESSED,
    PRIMARY_TEXT,
    SECONDARY_TEXT,
    TEXT_MUTED,
    ERROR,
)


class PresentationControls(QFrame):

    previous_clicked = Signal()
    start_clicked = Signal()
    next_clicked = Signal()
    end_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("PresentationControls")

        self.setStyleSheet(f"""
            QFrame#PresentationControls {{
                background-color: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 16px;
            }}

            QLabel#SectionTitle {{
                color: {PRIMARY_TEXT};
                font-size: 16px;
                font-weight: 600;
            }}

            QLabel#SectionSubtitle {{
                color: {SECONDARY_TEXT};
                font-size: 12px;
            }}

            QPushButton {{
                background-color: rgba(255, 255, 255, 0.04);
                color: {PRIMARY_TEXT};
                border: 1px solid {BORDER};
                border-radius: 10px;
                font-size: 12px;
                font-weight: 600;
                padding: 10px 16px;
            }}

            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.16);
            }}

            QPushButton:pressed {{
                background-color: rgba(255, 255, 255, 0.03);
            }}

            QPushButton#StartButton {{
                background-color: {PRIMARY};
                color: white;
                border: none;
            }}

            QPushButton#StartButton:hover {{
                background-color: {PRIMARY_HOVER};
            }}

            QPushButton#StartButton:pressed {{
                background-color: {PRIMARY_PRESSED};
            }}

            QPushButton#EndButton {{
                background-color: rgba(239, 68, 68, 0.10);
                color: {ERROR};
                border: 1px solid rgba(239, 68, 68, 0.25);
            }}

            QPushButton#EndButton:hover {{
                background-color: rgba(239, 68, 68, 0.20);
                border: 1px solid rgba(239, 68, 68, 0.40);
                color: #FCA5A5;
            }}
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
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
)

from frontend.styles.theme import (
    BG_DARK,
    SURFACE,
    BORDER,
    PRIMARY_TEXT,
    SECONDARY_TEXT,
    TEXT_MUTED,
)


class StudioPage(QWidget):

    back_requested = Signal()

    def __init__(
        self,
        title: str,
        subtitle: str,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)

        self.setObjectName("StudioPage")
        self.setAttribute(Qt.WA_StyledBackground, True)

        self.setStyleSheet(f"""
        QWidget#StudioPage {{
            background-color: {BG_DARK};
        }}

        QFrame#ContentFrame {{
            background: {SURFACE};
            border: 1px solid {BORDER};
            border-radius: 16px;
        }}
        """)

        main = QVBoxLayout(self)
        main.setContentsMargins(40, 32, 40, 32)
        main.setSpacing(24)

        # ---------- Header ----------

        header = QHBoxLayout()

        left = QVBoxLayout()
        left.setSpacing(4)

        self.back_btn = QPushButton("← Back")
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.clicked.connect(self.back_requested.emit)

        self.back_btn.setStyleSheet(f"""
        QPushButton {{
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid {BORDER};
            border-radius: 8px;
            color: {PRIMARY_TEXT};
            font-size: 12px;
            font-weight: 600;
            padding: 6px 14px;
        }}

        QPushButton:hover {{
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.16);
            color: #FFFFFF;
        }}
        """)

        left.addWidget(self.back_btn, 0, Qt.AlignLeft)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"""
            color: {PRIMARY_TEXT};
            font-size: 26px;
            font-weight: 700;
            letter-spacing: -0.4px;
        """)

        left.addWidget(self.title_label)

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setStyleSheet(f"""
            color: {SECONDARY_TEXT};
            font-size: 14px;
        """)

        left.addWidget(self.subtitle_label)

        header.addLayout(left)
        header.addStretch()

        main.addLayout(header)

        # ---------- Content ----------

        content_frame = QFrame()
        content_frame.setObjectName("ContentFrame")

        self.content_layout = QVBoxLayout(content_frame)
        self.content_layout.setContentsMargins(24, 24, 24, 24)
        self.content_layout.setSpacing(20)

        main.addWidget(content_frame, 1)

        # ---------- Status ----------

        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet(f"""
            color: {TEXT_MUTED};
            font-size: 12px;
        """)

        main.addWidget(self.status_label)
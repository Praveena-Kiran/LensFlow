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

        self.setStyleSheet("""
        QWidget#StudioPage{
            background-color:#0B0B0F;
        }

        QFrame#ContentFrame{
            background:#16161E;
            border-radius:16px;
        }
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

        self.back_btn.setStyleSheet("""
        QPushButton{
            background:transparent;
            border:none;
            color:#60A5FA;
            font-size:13px;
            font-weight:600;
            text-align:left;
        }

        QPushButton:hover{
            color:#93C5FD;
        }
        """)

        left.addWidget(self.back_btn, 0, Qt.AlignLeft)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("""
            color:white;
            font-size:28px;
            font-weight:700;
        """)

        left.addWidget(self.title_label)

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setStyleSheet("""
            color:#9CA3AF;
            font-size:14px;
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
        self.status_label.setStyleSheet("""
            color:#9CA3AF;
            font-size:12px;
        """)

        main.addWidget(self.status_label)
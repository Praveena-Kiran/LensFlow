from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
)

from frontend.pages.studio_page import StudioPage

from backend.automation.flow_manager import FlowManager


class CodingPage(StudioPage):
    """Coding Studio workspace."""

    def __init__(self, parent: Optional[QWidget] = None):

        super().__init__(
            "Coding Studio",
            "Launch your development workspace and AI coding tools.",
            parent,
        )

        # ---------------------------------------------------------
        # Flow Manager
        # ---------------------------------------------------------

        self.flow_manager = FlowManager()

        # ---------------------------------------------------------
        # Workspace header
        # ---------------------------------------------------------

        workspace_frame = QFrame()

        workspace_frame.setStyleSheet("""
            QFrame {
                background-color: #111118;
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 14px;
            }
        """)

        workspace_layout = QVBoxLayout(
            workspace_frame
        )

        workspace_layout.setContentsMargins(
            20,
            20,
            20,
            20
        )

        workspace_layout.setSpacing(14)

        # ---------------------------------------------------------
        # Title
        # ---------------------------------------------------------

        title = QLabel(
            "Development Workspace"
        )

        title.setStyleSheet("""
            color: white;
            font-size: 16px;
            font-weight: 600;
        """)

        workspace_layout.addWidget(
            title
        )

        # ---------------------------------------------------------
        # Description
        # ---------------------------------------------------------

        description = QLabel(
            "Launch the tools you need to start coding."
        )

        description.setStyleSheet("""
            color: #6B7280;
            font-size: 13px;
        """)

        workspace_layout.addWidget(
            description
        )

        # ---------------------------------------------------------
        # Buttons
        # ---------------------------------------------------------

        buttons_layout = QHBoxLayout()

        buttons_layout.setSpacing(
            12
        )

        self.launch_button = QPushButton(
            "▶  Launch Workspace"
        )

        self.launch_button.setCursor(
            Qt.PointingHandCursor
        )

        self.launch_button.setFixedHeight(
            42
        )

        self.launch_button.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 9px;
                padding: 0 20px;
                font-size: 13px;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #34D399;
            }

            QPushButton:pressed {
                background-color: #059669;
            }

            QPushButton:disabled {
                background-color: #374151;
                color: #9CA3AF;
            }
        """)

        buttons_layout.addWidget(
            self.launch_button
        )

        buttons_layout.addStretch()

        workspace_layout.addLayout(
            buttons_layout
        )

        self.content_layout.addWidget(
            workspace_frame
        )

        # ---------------------------------------------------------
        # Applications panel
        # ---------------------------------------------------------

        apps_frame = QFrame()

        apps_frame.setStyleSheet("""
            QFrame {
                background-color: #111118;
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 14px;
            }
        """)

        apps_layout = QVBoxLayout(
            apps_frame
        )

        apps_layout.setContentsMargins(
            20,
            20,
            20,
            20
        )

        apps_layout.setSpacing(
            10
        )

        # ---------------------------------------------------------
        # Applications title
        # ---------------------------------------------------------

        apps_title = QLabel(
            "Workspace Applications"
        )

        apps_title.setStyleSheet("""
            color: white;
            font-size: 15px;
            font-weight: 600;
        """)

        apps_layout.addWidget(
            apps_title
        )

        # ---------------------------------------------------------
        # Applications
        # ---------------------------------------------------------

        applications = [
            ("VS Code", "Code editor"),
            ("Terminal", "Command line"),
            ("Git", "Version control"),
        ]

        for name, description_text in applications:

            row = QFrame()

            row.setStyleSheet("""
                QFrame {
                    background-color: #181820;
                    border-radius: 9px;
                }
            """)

            row_layout = QHBoxLayout(
                row
            )

            row_layout.setContentsMargins(
                14,
                10,
                14,
                10
            )

            name_label = QLabel(
                name
            )

            name_label.setStyleSheet("""
                color: #F9FAFB;
                font-size: 13px;
                font-weight: 600;
            """)

            description_label = QLabel(
                description_text
            )

            description_label.setStyleSheet("""
                color: #6B7280;
                font-size: 12px;
            """)

            row_layout.addWidget(
                name_label
            )

            row_layout.addStretch()

            row_layout.addWidget(
                description_label
            )

            apps_layout.addWidget(
                row
            )

        self.content_layout.addWidget(
            apps_frame
        )

        # ---------------------------------------------------------
        # Connections
        # ---------------------------------------------------------

        self.launch_button.clicked.connect(
            self._launch_workspace
        )

    # =============================================================
    # Launch Coding Workspace
    # =============================================================

    def _launch_workspace(self):

        print(
            "🚀 Launching Coding Workspace"
        )

        # Update UI
        self.status_label.setText(
            "Status: Launching workspace..."
        )

        self.status_label.setStyleSheet("""
            color: #60A5FA;
            font-size: 12px;
        """)

        # Prevent double-click launches
        self.launch_button.setEnabled(
            False
        )

        try:

            # -----------------------------------------------------
            # Execute coding_flow from flows.json
            # -----------------------------------------------------

            self.flow_manager.execute_flow(
                "coding_flow"
            )

            # -----------------------------------------------------
            # Success
            # -----------------------------------------------------

            self.status_label.setText(
                "Status: Workspace launched"
            )

            self.status_label.setStyleSheet("""
                color: #34D399;
                font-size: 12px;
            """)

            print(
                "✅ Coding Workspace launched"
            )

        except Exception as e:

            # -----------------------------------------------------
            # Error
            # -----------------------------------------------------

            self.status_label.setText(
                "Status: Launch failed"
            )

            self.status_label.setStyleSheet("""
                color: #F87171;
                font-size: 12px;
            """)

            print(
                f"❌ Coding Workspace Error: {e}"
            )

        finally:

            self.launch_button.setEnabled(
                True
            )
            
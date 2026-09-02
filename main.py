"""
LensFlow — Premium Desktop Workspace Operating System

Main application window.
"""

from mediapipe.python.solutions import selfie_segmentation
import sys
import os

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
)

from PySide6.QtCore import (
    Qt,
    QFile,
    QTextStream,
    QThread,
)

from PySide6.QtGui import QFont

from frontend.components.title_bar import TitleBar
from frontend.components.sidebar import AppSidebar

from frontend.pages.home import HomePage
from frontend.pages.presentation_page import PresentationPage
from frontend.pages.coding_page import CodingPage
from frontend.pages.gesture_page import GesturePage
from frontend.pages.custom_page import CustomPage

from backend.gestures.gesture_worker import GestureWorker
from backend.automation.action_manager import ActionManager


# =============================================================
# ROOT PATH
# =============================================================

sys.path.insert(
    0,
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "LensFlow"
        )

        # =====================================================
        # WINDOW
        # =====================================================

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Window
        )

        screen = (
            QApplication
            .primaryScreen()
            .availableGeometry()
        )

        width = int(
            screen.width() * 0.85
        )

        height = int(
            screen.height() * 0.85
        )

        self.setMinimumSize(
            1100,
            700
        )

        self.resize(
            width,
            height
        )

        self._center_on_screen()

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground,
            False
        )

        self.setStyleSheet(
            "background-color: #0B0B0F;"
        )

        # =====================================================
        # ROOT
        # =====================================================

        root = QWidget()

        self.setCentralWidget(
            root
        )

        root_layout = QVBoxLayout(
            root
        )

        root_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        root_layout.setSpacing(
            0
        )

        # =====================================================
        # TITLE BAR
        # =====================================================

        self.title_bar = TitleBar(
            self
        )

        root_layout.addWidget(
            self.title_bar
        )

        # =====================================================
        # BODY
        # =====================================================

        body = QHBoxLayout()

        body.setContentsMargins(
            0,
            0,
            0,
            0
        )

        body.setSpacing(
            0
        )

        # =====================================================
        # SIDEBAR
        # =====================================================

        self.sidebar = AppSidebar()

        body.addWidget(
            self.sidebar
        )

        # =====================================================
        # STACK
        # =====================================================

        self.stack = QStackedWidget()

        # =====================================================
        # PAGES
        # =====================================================

        self.home_page = HomePage()

        self.presentation_page = (
            PresentationPage()
        )

        self.coding_page = (
            CodingPage()
        )

        self.gesture_page = (
            GesturePage()
        )

        self.custom_page = (
            CustomPage()
        )

        # =====================================================
        # ADD PAGES
        # =====================================================

        self.stack.addWidget(
            self.home_page
        )

        self.stack.addWidget(
            self.presentation_page
        )

        self.stack.addWidget(
            self.coding_page
        )

        self.stack.addWidget(
            self.gesture_page
        )

        self.stack.addWidget(
            self.custom_page
        )

        body.addWidget(
            self.stack,
            1
        )

        # =====================================================
        # GESTURE SYSTEM
        # =====================================================

        self.gesture_thread = None

        self.gesture_worker = None

        self.action_manager = (
            ActionManager()
        )

        # =====================================================
        # HOME → STUDIO
        # =====================================================

        self.home_page.studio_selected.connect(
            self.open_live_workspace
        )

        # =====================================================
        # HOME → CREATE STUDIO
        # =====================================================

        self.home_page.create_studio_requested.connect(
            self.create_custom_studio
        )

        # =====================================================
        # CUSTOM → HOME
        # =====================================================

        self.custom_page.back_requested.connect(
            self.go_home
        )

        # =====================================================
        # CUSTOM SAVED
        # =====================================================

        self.custom_page.studio_saved.connect(
            self.refresh_home
        )

        # =====================================================
        # PRESENTATION → HOME
        # =====================================================

        self.presentation_page.back_requested.connect(
            self.go_home
        )

        # =====================================================
        # CODING → HOME
        # =====================================================

        self.coding_page.back_requested.connect(
            self.go_home
        )

        # =====================================================
        # GESTURE → HOME
        # =====================================================

        self.gesture_page.back_requested.connect(
            self.go_home
        )

        # =====================================================
        # FINISH
        # =====================================================

        root_layout.addLayout(
            body,
            1
        )

        self.showNormal()

    # =============================================================
    # CENTER
    # =============================================================

    def _center_on_screen(
        self
    ):

        screen = (
            QApplication
            .primaryScreen()
            .availableGeometry()
        )

        x = (
            screen.x()
            + (
                screen.width()
                - self.width()
            ) // 2
        )

        y = (
            screen.y()
            + (
                screen.height()
                - self.height()
            ) // 2
        )

        self.move(
            x,
            y
        )

    # =============================================================
    # HOME
    # =============================================================

    def go_home(self):
        self.home_page.refresh_studios()

        self.stack.setCurrentWidget(
            self.home_page
        )

    # =============================================================
    # REFRESH HOME
    # =============================================================

    def refresh_home(
        self
    ):

        self.home_page.refresh_studios()

    # =============================================================
    # CREATE CUSTOM STUDIO
    # =============================================================

    def create_custom_studio(
        self
    ):

        print(
            "🛠 Creating Custom Studio"
        )

        # Open dialog to ask for name

        from PySide6.QtWidgets import (
            QDialog,
            QVBoxLayout,
            QLabel,
            QLineEdit,
            QDialogButtonBox,
        )

        dialog = QDialog(
            self
        )

        dialog.setWindowTitle(
            "Create Studio"
        )

        dialog.setMinimumWidth(
            400
        )

        dialog.setStyleSheet("""
            QDialog {
                background: #16161E;
            }

            QLabel {
                color: white;
                font-size: 13px;
            }

            QLineEdit {
                background: #20202A;
                color: white;
                border: 1px solid #363646;
                border-radius: 8px;
                padding: 10px;
            }

            QDialogButtonBox QPushButton {
                background: #2563EB;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
            }
        """)

        layout = QVBoxLayout(
            dialog
        )

        layout.setContentsMargins(
            24,
            24,
            24,
            24
        )

        layout.setSpacing(
            12
        )

        layout.addWidget(
            QLabel(
                "Studio Name"
            )
        )

        name_input = QLineEdit()

        name_input.setPlaceholderText(
            "e.g. Gaming Studio"
        )

        layout.addWidget(
            name_input
        )

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Ok
        )

        buttons.accepted.connect(
            dialog.accept
        )

        buttons.rejected.connect(
            dialog.reject
        )

        layout.addWidget(
            buttons
        )

        if (
            dialog.exec()
            != QDialog.DialogCode.Accepted
        ):

            return

        name = (
            name_input
            .text()
            .strip()
        )

        if not name:

            return

        # =====================================================
        # CREATE STUDIO IN MEMORY
        # =====================================================

        self.custom_page.start_new_studio(
            name
        )

        # =====================================================
        # OPEN CUSTOM EDITOR
        # =====================================================

        self.stack.setCurrentWidget(
            self.custom_page
        )

    # =============================================================
    # STUDIO NAVIGATION
    # =============================================================

    def open_live_workspace(
        self,
        studio_name
    ):

        print(
            "CLICKED:",
            studio_name
        )

        # -----------------------------------------------------
        # PRESENTATION
        # -----------------------------------------------------

        if studio_name == "Presentation Studio":

            self.stack.setCurrentWidget(
                self.presentation_page
            )

            self.start_gesture_worker(
                "presentation"
            )

        # -----------------------------------------------------
        # CODING
        # -----------------------------------------------------

        elif studio_name == "Coding Studio":

            self.stack.setCurrentWidget(
                self.coding_page
            )

        # -----------------------------------------------------
        # GESTURE
        # -----------------------------------------------------

        elif studio_name == "Gesture Studio":

            self.stack.setCurrentWidget(
                self.gesture_page
            )

        # -----------------------------------------------------
        # CUSTOM
        # -----------------------------------------------------

        else:

            # Check whether it is a custom studio

            if self.custom_page.load_studio(
                studio_name
            ):

                print(
                    f"🛠 Editing custom studio: "
                    f"{studio_name}"
                )

                self.stack.setCurrentWidget(
                    self.custom_page
                )

            else:

                print(
                    f"⚠ No workspace configured for: "
                    f"{studio_name}"
                )

    # =============================================================
    # GESTURE WORKER
    # =============================================================

    def start_gesture_worker(
        self,
        profile_name
    ):

        print(
            f"🎯 Starting gesture profile: "
            f"{profile_name}"
        )

        if self.gesture_thread is not None:

            if self.gesture_thread.isRunning():

                print(
                    "⚠ Gesture worker already running."
                )

                return

        self.gesture_thread = QThread()

        self.gesture_worker = (
            GestureWorker(
                profile_name
            )
        )

        self.gesture_worker.moveToThread(
            self.gesture_thread
        )

        self.gesture_thread.started.connect(
            self.gesture_worker.run
        )

        self.gesture_worker.error.connect(
            lambda message:
            print(
                f"❌ Gesture Error: {message}"
            )
        )

        self.gesture_worker.gesture_detected.connect(
            lambda gesture, confidence:
            print(
                f"Detected: {gesture} | "
                f"Confidence: {confidence:.2f}"
            )
        )

        self.gesture_worker.action_detected.connect(
            self.handle_gesture_action
        )

        self.gesture_worker.status_changed.connect(
            lambda status:
            print(
                f"Gesture Status: {status}"
            )
        )

        self.gesture_thread.start()

    # =============================================================
    # GESTURE ACTION
    # =============================================================

    def handle_gesture_action(
        self,
        action
    ):

        print(
            f"🎯 Gesture action: {action}"
        )

        self.action_manager.execute(
            "",
            action
        )


# =============================================================
# STYLESHEET
# =============================================================

def _load_stylesheet(
    app
):

    qss_path = os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
        ),
        "frontend",
        "styles",
        "theme.qss"
    )

    file = QFile(
        qss_path
    )

    if file.open(
        QFile.OpenModeFlag.ReadOnly
        | QFile.OpenModeFlag.Text
    ):

        stream = QTextStream(
            file
        )

        app.setStyleSheet(
            stream.readAll()
        )

        file.close()


# =============================================================
# MAIN
# =============================================================

def main():

    app = QApplication(
        sys.argv
    )

    app.setFont(
        QFont(
            "Inter",
            14
        )
    )

    _load_stylesheet(
        app
    )

    window = MainWindow()

    window.show()

    window._center_on_screen()

    sys.exit(
        app.exec()
    )


# =============================================================
# ENTRY POINT
# =============================================================

if __name__ == "__main__":

    main()
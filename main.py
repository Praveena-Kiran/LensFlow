"""LensFlow — Premium Desktop Workspace Operating System

Frameless main window with custom title bar, sidebar navigation,
and the Home page as the default view.
"""

from mediapipe.python.solutions import selfie_segmentation
from mediapipe.python.solutions import selfie_segmentation
from mediapipe.python.solutions import selfie_segmentation
from mediapipe.python.solutions import selfie_segmentation
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, QFile, QTextStream
from PySide6.QtGui import QFont

from frontend.components.title_bar import TitleBar
from frontend.components.sidebar import AppSidebar
from frontend.pages.home import HomePage
from frontend.components.title_bar import TitleBar
from frontend.pages.presentation_page import PresentationPage
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
)
from frontend.pages.presentation_page import PresentationPage
from PySide6.QtCore import QThread
from backend.gestures.gesture_worker import GestureWorker
from backend.automation.action_manager import ActionManager
class MainWindow(QMainWindow):
    """LensFlow frameless main window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("LensFlow")
    
        # Frameless window
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window
        )
        screen = QApplication.primaryScreen().availableGeometry()
        width = int(screen.width() * 0.85)
        height = int(screen.height() * 0.85)

        self.setMinimumSize(1100, 700)
        self.resize(width, height)
        self._center_on_screen()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setStyleSheet("background-color: #0B0B0F;")

        # ── Root Widget ─────────────────────────────────────────────────
        root = QWidget()
        self.setCentralWidget(root)

        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Title Bar ───────────────────────────────────────────────────
        self.title_bar = TitleBar(self)
        root_layout.addWidget(self.title_bar)

        # ── Body: Sidebar + Page Content ────────────────────────────────
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self.sidebar = AppSidebar()
        body.addWidget(self.sidebar)

        self.stack = QStackedWidget()

        self.home_page = HomePage()
        self.presentation_page = PresentationPage()
        self.gesture_thread = None
        self.gesture_worker = None
        self.action_manager = ActionManager()

        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.presentation_page)

        body.addWidget(self.stack, 1)

        self.home_page.studio_selected.connect(
            self.open_live_workspace
        )

        self.presentation_page.back_requested.connect(
            lambda: self.stack.setCurrentWidget(self.home_page)
        )


        root_layout.addLayout(body, 1)
        self.showNormal()


    def launch_studio(self, studio_name):
        print(f"Launching Studio: {studio_name}")
    
    
    def _center_on_screen(self):
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.x() + (screen.width() - self.width()) // 2
        y = screen.y() + (screen.height() - self.height()) // 2
        self.move(x, y)

    def open_live_workspace(self, studio_name):
        print("CLICKED:", studio_name)

        if studio_name == "Presentation Studio":
            print("SWITCHING TO PRESENTATION")

            self.stack.setCurrentWidget(
                self.presentation_page
            )

            self.start_gesture_worker(
                "presentation"
            )

    
    def start_gesture_worker(self, profile_name):
        print(f"🎯 Starting gesture profile: {profile_name}")

        self.gesture_thread = QThread()
        self.gesture_worker = GestureWorker(profile_name)

        self.gesture_worker.moveToThread(self.gesture_thread)

        self.gesture_thread.started.connect(
            self.gesture_worker.run
        )

        self.gesture_worker.error.connect(
            lambda message: print(f"❌ Gesture Error: {message}")
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
                print(f"Gesture Status: {status}")
        )

        self.gesture_thread.start()
    
    def handle_gesture_action(self, action):
        print(f"🎯 Gesture action: {action}")
        self.action_manager.execute(
            "",
            action
        )


def _load_stylesheet(app: QApplication):
    qss_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "frontend", "styles", "theme.qss"
    )
    f = QFile(qss_path)
    if f.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
        stream = QTextStream(f)
        app.setStyleSheet(stream.readAll())
        f.close()


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Inter", 14))
    _load_stylesheet(app)

    window = MainWindow()
    window.show()
    window._center_on_screen()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

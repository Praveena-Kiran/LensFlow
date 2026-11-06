"""
LensFlow — Premium Desktop Workspace Operating System

Main application window.
"""

import sys
import datetime
import time
import os

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
    QDialog,
    QLabel,
    QLineEdit,
    QDialogButtonBox,
    QMenu,
    QMessageBox,
    QSystemTrayIcon,
)

from PySide6.QtCore import (
    Qt,
    Slot,
    QFile,
    QTextStream,
    QProcess,
    QThread,
    QTimer,
)

from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPen, QPixmap

from frontend.components.title_bar import TitleBar
from frontend.components.sidebar import AppSidebar

from frontend.pages.home import HomePage
from frontend.pages.presentation_page import PresentationPage
from frontend.pages.coding_page import CodingPage
from frontend.pages.gesture_page import GesturePage
from frontend.pages.custom_page import CustomPage
from frontend.pages.settings_page import SettingsPage
from frontend.pages.activity_page import ActivityPage
from frontend.pages.notifications_page import NotificationsPage
from frontend.components.suggestion_dialog import SuggestionDialog
from backend import startup
from backend.routines import (
    ActivityLog,
    RoutineStore,
    due_routines,
    suggest_routines,
)
from backend.settings.settings_manager import SettingsManager
from frontend.styles.theme import (
    ON_PRIMARY,
    BG_DARK,
    SURFACE,
    BORDER,
    PRIMARY,
    PRIMARY_HOVER,
    PRIMARY_TEXT,
    SECONDARY_TEXT,
)

from backend.gestures.gesture_worker import GestureWorker
from backend.automation.action_manager import ActionManager
from frontend.styles.theme import BG_DARK, ERROR, PRIMARY, global_stylesheet
from frontend.components.backdrop import BackdropWidget
from backend.paths import APP_DIR


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

        # Scoped to the window: an unscoped rule here would cascade to
        # every widget and hide the theme's backdrop.
        self.setStyleSheet(
            f"QMainWindow {{ background-color: {BG_DARK}; }}"
        )

        # =====================================================
        # ROOT (paints the theme background: plain, stars or leaves)
        # =====================================================

        root = BackdropWidget()

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

        self.settings_page = SettingsPage()

        self.activity_page = ActivityPage()

        self.notifications_page = NotificationsPage()

        # =====================================================
        # ADD PAGES
        # =====================================================

        self.stack.addWidget(
            self.home_page
        )

        self.stack.addWidget(
            self.settings_page
        )

        self.stack.addWidget(
            self.activity_page
        )

        self.stack.addWidget(
            self.notifications_page
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

        # Which studio page started the gesture worker ("custom",
        # "presentation", ...) and its name, for status messages.
        self.gesture_context = None

        self.gesture_studio_name = ""

        self._last_event_run = {}

        # Stopped camera threads that are still shutting down.
        self._retiring_threads = []

        self.action_manager = (
            ActionManager()
        )

        # =====================================================
        # HOME → BUILT-IN STUDIO
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
        # HOME → CUSTOM STUDIO EXECUTION
        # =====================================================

        self.home_page.launch_all_events_requested.connect(
            self.launch_all_events
        )

        self.home_page.launch_specific_event_requested.connect(
            self.launch_specific_event
        )

        # =====================================================
        # CUSTOM → HOME
        # =====================================================

        self.custom_page.back_requested.connect(
            self.go_home
        )

        # =====================================================
        # CUSTOM → SAVE
        # =====================================================

        self.custom_page.studio_saved.connect(
            self.refresh_home
        )

        # =====================================================
        # CUSTOM → GESTURE CONTROL
        # =====================================================

        self.custom_page.gesture_control_started.connect(
            self.start_custom_gesture_control
        )

        self.custom_page.gesture_control_stopped.connect(
            self.stop_gesture_worker
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

        self.settings_page.back_requested.connect(
            self.go_home
        )

        self.settings_page.restart_requested.connect(
            self.restart_app
        )

        self.activity_page.back_requested.connect(
            self.go_home
        )

        self.notifications_page.back_requested.connect(
            self.go_home
        )

        self.notifications_page.changed.connect(
            self._refresh_suggestion
        )

        self.notifications_page.suggestion_accepted.connect(
            self._after_accept
        )

        self.home_page.history_requested.connect(
            lambda: self._on_sidebar("history")
        )

        self.settings_page.name_changed.connect(
            self._on_name_changed
        )

        # =====================================================
        # ROUTINES
        # =====================================================

        self._setup_routines()

        # =====================================================
        # SYSTEM TRAY
        # =====================================================

        self._setup_tray()

        # =====================================================
        # SIDEBAR NAVIGATION
        # =====================================================

        self.sidebar.item_selected.connect(
            self._on_sidebar
        )

        # =====================================================
        # FINISH ROOT LAYOUT
        # =====================================================

        root_layout.addLayout(
            body,
            1
        )

        self.showNormal()

    # =============================================================
    # CENTER WINDOW
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
    # SIDEBAR
    # =============================================================

    def _on_sidebar(
        self,
        item_id
    ):

        if item_id == "settings":
            self.stop_gesture_worker()
            self.stack.setCurrentWidget(self.settings_page)

        elif item_id == "history":
            self.stop_gesture_worker()
            self.sidebar.set_active("history")
            self.stack.setCurrentWidget(self.activity_page)

        elif item_id == "notifications":
            self.stop_gesture_worker()
            self.sidebar.set_active("notifications")
            self.stack.setCurrentWidget(self.notifications_page)

        else:
            # Home and Studios both show the dashboard of studios.
            self.go_home()

    # =============================================================
    # GO HOME
    # =============================================================

    def go_home(
        self
    ):

        print(
            "🏠 Returning to dashboard..."
        )

        self.stop_gesture_worker()

        self.sidebar.set_active("home")

        self.home_page.refresh_studios()

        self._refresh_suggestion()

        self.stack.setCurrentWidget(
            self.home_page
        )

    # =============================================================
    # REFRESH HOME
    # =============================================================

    def refresh_home(
        self
    ):

        print(
            "🔄 Refreshing dashboard..."
        )

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

        # =====================================================
        # DIALOG
        # =====================================================

        dialog = QDialog(
            self
        )

        dialog.setWindowTitle(
            "Create Studio"
        )

        dialog.setMinimumWidth(
            400
        )

        dialog.setStyleSheet(f"""
            QDialog {{
                background: {SURFACE};
                border: 1px solid {BORDER};
            }}

            QLabel {{
                color: {PRIMARY_TEXT};
                font-size: 13px;
            }}

            QLineEdit {{
                background: {BG_DARK};
                color: {PRIMARY_TEXT};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 10px;
            }}

            QLineEdit:focus {{
                border: 1px solid {PRIMARY};
            }}

            QDialogButtonBox QPushButton {{
                background: {PRIMARY};
                color: {ON_PRIMARY};
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
            }}

            QDialogButtonBox QPushButton:hover {{
                background: {PRIMARY_HOVER};
            }}
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

        # =====================================================
        # SHOW DIALOG
        # =====================================================

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
        # CREATE STUDIO
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

        # Gesture Studio is a settings area, not something to automate.
        if studio_name != "Gesture Studio":
            self._record("studio", studio_name, studio=studio_name)

        # =====================================================
        # PRESENTATION
        # =====================================================

        if studio_name == "Presentation Studio":

            self.stack.setCurrentWidget(
                self.presentation_page
            )

            self.start_gesture_worker(
                "presentation"
            )

        # =====================================================
        # CODING
        # =====================================================

        elif studio_name == "Coding Studio":

            self.stack.setCurrentWidget(
                self.coding_page
            )

        # =====================================================
        # GESTURE
        # =====================================================

        elif studio_name == "Gesture Studio":

            self.stack.setCurrentWidget(
                self.gesture_page
            )

        # =====================================================
        # CUSTOM STUDIO
        # =====================================================

        else:

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
    # LAUNCH ALL CUSTOM EVENTS
    # =============================================================

    def launch_all_events(self, studio_name):
        print(f"🚀 Launching ALL events: {studio_name}")

        self._record("launch", studio_name, studio=studio_name)

        studios = self.home_page.load_studios()

        studio = next(
            (
                s for s in studios
                if isinstance(s, dict)
                and s.get("title") == studio_name
            ),
            None
        )

        if not studio:
            print(f"❌ Could not find studio: {studio_name}")
            return

        events = studio.get("events", [])

        if not events:
            print("⚠️ This studio has no events.")
            return

        for event in events:
            try:
                self.action_manager.flow_manager.execute_custom_event(
                    event
                )
            except Exception as e:
                print(f"❌ Event failed: {e}")

    # =============================================================
    # LAUNCH SPECIFIC CUSTOM EVENT
    # =============================================================

    def launch_specific_event(
        self,
        studio_name,
        event
    ):

        event_name = (
            event.get(
                "name",
                "Unnamed Event"
            )
            if isinstance(event, dict)
            else "Invalid Event"
        )

        if isinstance(event, dict):
            self._record("event", event_name, studio=studio_name, event=event)

        print(
            ""
        )

        print(
            "========================================"
        )

        print(
            f"🎯 LAUNCHING EVENT: {event_name}"
        )

        print(
            f"📁 STUDIO: {studio_name}"
        )

        print(
            "========================================"
        )

        if not isinstance(
            event,
            dict
        ):

            print(
                "❌ Invalid event."
            )

            return

        try:

            self.action_manager.flow_manager.execute_custom_event(
                event
            )

            print(
                f"✅ Event completed: {event_name}"
            )

        except Exception as e:

            print(
                f"❌ Event failed: {event_name}"
            )

            print(
                f"   {e}"
            )

    # =============================================================
    # GESTURE WORKER
    # =============================================================

    def start_custom_gesture_control(
        self,
        studio
    ):

        self.start_gesture_worker(
            "custom",
            custom_studio=studio
        )

    # =============================================================
    # GESTURE WORKER
    # =============================================================
    # One worker for every studio. It emits events (see
    # backend/automation/events.py); _on_gesture_event runs them and
    # status goes to whichever studio page started the worker.

    EVENT_COOLDOWN = 0.8   # seconds before the same event can run again

    def start_gesture_worker(
        self,
        profile_name,
        custom_studio=None
    ):

        # Only one thing can use the camera; stop anything already running.
        self.stop_gesture_worker()

        print(
            f"🎯 Starting gestures: "
            f"{custom_studio.get('title') if custom_studio else profile_name}"
        )

        self.gesture_context = (
            "custom" if custom_studio is not None else profile_name
        )

        self.gesture_studio_name = (
            custom_studio.get("title", "")
            if custom_studio is not None
            else profile_name.title()
        )

        self._last_event_run = {}

        try:

            worker = GestureWorker(
                profile_name,
                custom_studio=custom_studio
            )

        except Exception as e:

            print(f"❌ Could not start gestures: {e}")

            self._gesture_feedback(f"⚠ Could not start gestures: {e}", ERROR)

            return

        self.gesture_thread = QThread()

        self.gesture_worker = worker

        self.gesture_worker.moveToThread(
            self.gesture_thread
        )

        self.gesture_thread.started.connect(
            self.gesture_worker.run
        )

        # When the camera loop exits, end the thread's event loop too.
        # Direct connection: quit() runs on the worker thread itself, so this
        # works even while the UI thread is blocked waiting (closeEvent).
        self.gesture_worker.finished.connect(
            self.gesture_thread.quit,
            Qt.ConnectionType.DirectConnection
        )

        # Bound methods (not lambdas) so these run on the UI thread.
        self.gesture_worker.custom_event_detected.connect(
            self._on_gesture_event
        )

        self.gesture_worker.gesture_detected.connect(
            self._on_gesture_seen
        )

        self.gesture_worker.status_changed.connect(
            self._on_gesture_status
        )

        self.gesture_worker.error.connect(
            self._on_gesture_error
        )

        if self.gesture_context == "custom":
            self.custom_page.set_gesture_control_running(
                True,
                "Starting camera…"
            )
        else:
            self._gesture_feedback("Starting camera…")

        self.gesture_thread.start()

    def _gesture_feedback(
        self,
        message,
        color=None
    ):

        context = getattr(self, "gesture_context", None)

        if context == "custom":
            self.custom_page.show_gesture_feedback(message, color)

        elif context == "presentation":
            if color:
                self.presentation_page._set_status(message, color)
            else:
                self.presentation_page._set_status(message)

    @Slot(dict)
    def _on_gesture_event(
        self,
        event
    ):

        gesture = event.get("gesture", "")
        name = event.get("name", "event")

        now = time.monotonic()

        if now - self._last_event_run.get(name, 0) < self.EVENT_COOLDOWN:
            return

        self._last_event_run[name] = now

        print(
            f"🎯 {gesture} → {name} "
            f"({self.gesture_studio_name})"
        )

        self._record(
            "event",
            name,
            studio=self.gesture_studio_name,
            event=event,
            trigger="gesture",
        )

        try:

            self.action_manager.flow_manager.execute_custom_event(
                event
            )

        except Exception as e:

            print(f"❌ Event failed: {name}: {e}")

            self._gesture_feedback(
                f"{gesture}  →  {name} failed: {e}",
                ERROR
            )

            return

        self._gesture_feedback(
            f"{gesture}  →  {name}"
        )

    @Slot(str, float)
    def _on_gesture_seen(
        self,
        gesture,
        confidence
    ):

        print(
            f"Detected: {gesture} | "
            f"Confidence: {confidence:.2f}"
        )

        if self.gesture_context == "custom":
            self._gesture_feedback(
                f"Saw {gesture} ({int(confidence * 100)}%)"
            )

    @Slot(str)
    def _on_gesture_status(
        self,
        status
    ):

        worker = self.gesture_worker

        arm_hint = (
            f"Make {worker.arm_gesture} to activate gestures"
            if worker is not None and worker.require_arm
            else None
        )

        if status == "READY":
            self._gesture_feedback(arm_hint or "Listening for gestures…")

        elif status == "ARMED":
            self._gesture_feedback("Gestures active")

        elif status == "DISARMED" and arm_hint:
            self._gesture_feedback(f"Paused. {arm_hint}")

    @Slot(str)
    def _on_gesture_error(
        self,
        message
    ):

        print(f"❌ Gesture Error: {message}")

        context = self.gesture_context

        self.stop_gesture_worker()

        if context == "custom":
            self.custom_page.set_gesture_control_running(
                False,
                f"⚠ {message}"
            )
        else:
            self.gesture_context = context
            self._gesture_feedback(f"⚠ {message}", ERROR)

    # =============================================================
    # STOP GESTURE WORKER
    # =============================================================

    def stop_gesture_worker(
        self
    ):

        if self.gesture_worker is None:

            return

        print(
            "🛑 Stopping gesture worker..."
        )

        try:

            # Ask the camera loop to finish. Called directly (not through a
            # signal) because the worker's thread is busy inside run().
            self.gesture_worker.stop()

        except Exception as e:

            print(
                f"⚠ Could not stop gesture worker: {e}"
            )

        # Don't block the UI waiting for the camera: on Windows releasing a
        # webcam can take several seconds. Keep the old thread alive in
        # `_retiring_threads` until it has really finished — destroying a
        # QThread that is still running makes Qt abort the whole app (this
        # was the Presentation Studio "Back" crash).
        thread = self.gesture_thread
        worker = self.gesture_worker

        if thread is not None:

            entry = (thread, worker)

            self._retiring_threads.append(entry)

            thread.finished.connect(
                lambda e=entry: self._forget_thread(e)
            )

            if not thread.isRunning():
                self._forget_thread(entry)

        self.gesture_worker = None

        self.gesture_thread = None

        self.gesture_context = None

        if self.custom_page.gesture_control_running:

            self.custom_page.set_gesture_control_running(
                False
            )

    def _forget_thread(
        self,
        entry
    ):

        if entry in self._retiring_threads:

            self._retiring_threads.remove(entry)

            entry[0].deleteLater()

    # =============================================================
    # WINDOW CLOSE
    # =============================================================

    def closeEvent(
        self,
        event
    ):

        # Keep running in the tray (so routines can fire) if the user chose
        # that, unless they picked Quit.
        if (
            not self._quitting
            and self.tray is not None
            and SettingsManager().get_setting("run_in_background")
        ):

            event.ignore()

            self.stop_gesture_worker()

            self.hide()

            if not self._told_about_tray:
                self._told_about_tray = True
                self.tray.showMessage(
                    "LensFlow is still running",
                    "Your routines will run on time. Right-click the tray "
                    "icon to quit.",
                    QSystemTrayIcon.MessageIcon.Information,
                    4000,
                )

            return

        # Let the camera thread finish before the app exits. Hide first so
        # closing feels instant even if the webcam is slow to release.
        self.hide()

        self.stop_gesture_worker()

        for thread, _worker in list(self._retiring_threads):

            if not thread.wait(5000):

                print(
                    "⚠ Camera thread did not stop before exit."
                )

        # The foggy window on Home has its own camera thread.
        self.home_page.fog.stop_camera()
        self.home_page.fog.wait_for_camera()

        if self.tray is not None:
            self.tray.hide()

        super().closeEvent(event)

        QApplication.instance().quit()

    # =============================================================
    # ROUTINES
    # =============================================================

    ROUTINE_CHECK_MS = 30_000

    def _setup_routines(self):

        self.activity_log = ActivityLog()
        self.routine_store = RoutineStore()

        # How the next recorded action was started ("click", "gesture",
        # "routine"). Routine runs are logged but never learned from.
        self._trigger_source = "click"

        try:
            self.activity_log.prune()
        except OSError:
            pass

        self.routine_timer = QTimer(self)
        self.routine_timer.timeout.connect(self._run_due_routines)
        self.routine_timer.start(self.ROUTINE_CHECK_MS)

        QTimer.singleShot(3000, self._run_due_routines)

        self._refresh_suggestion()

        # Ask about a new routine shortly after LensFlow opens.
        QTimer.singleShot(1200, self._show_suggestion_popup)

    def _record(
        self,
        kind,
        target,
        studio=None,
        event=None,
        trigger=None
    ):

        self.activity_log.record(
            kind,
            target,
            studio=studio,
            trigger=trigger or self._trigger_source,
            event=event,
        )

    def _pending_suggestions(self):

        try:
            self.routine_store.load()
            return suggest_routines(
                self.activity_log.entries(),
                self.routine_store,
            )
        except Exception as e:
            print(f"⚠ Could not check for routines: {e}")
            return []

    def _refresh_suggestion(self):
        """Update the Notifications count (suggestions waiting for an answer)."""

        self.sidebar.set_badge(
            "notifications",
            len(self._pending_suggestions())
        )

    def _show_suggestion_popup(self):
        """When LensFlow opens: offer the top new suggestion, once a day."""

        if not self.isVisible():
            return  # started in the tray; the badge waits for them

        for suggestion in self._pending_suggestions():

            if self.routine_store.was_prompted_today(suggestion):
                continue

            self.routine_store.mark_prompted(suggestion)

            dialog = SuggestionDialog(suggestion, self)

            if dialog.exec():
                self._accept_suggestion(suggestion)

            # "Not now": it stays in Notifications.
            break

        self._refresh_suggestion()

    def _accept_suggestion(
        self,
        suggestion
    ):

        self.routine_store.add(suggestion)

        self._after_accept(suggestion)

    @Slot(dict)
    def _after_accept(
        self,
        suggestion
    ):

        settings = SettingsManager()

        if not settings.get_setting("run_in_background") and not startup.is_enabled():

            answer = QMessageBox.question(
                self,
                "Keep LensFlow running?",
                "Automations only run while LensFlow is open. Keep it running "
                "in the system tray when you close the window?",
            )

            if answer == QMessageBox.Yes:
                settings.set_setting("run_in_background", True)

        self._refresh_suggestion()

        self.home_page.refresh_studios()

    def _on_name_changed(self):
        self.sidebar.refresh_user()
        self.home_page.refresh_studios()

    def _run_due_routines(self):

        self.routine_store.load()

        for routine in due_routines(self.routine_store.routines):

            print(f"⏰ Routine: {routine['kind']} {routine['target']}")

            self._trigger_source = "routine"

            try:

                if routine["kind"] == "studio":
                    self.show_from_tray()
                    self.open_live_workspace(routine["target"])

                elif routine["kind"] == "launch":
                    self.launch_all_events(routine["target"])

                elif routine.get("event"):
                    self.launch_specific_event(
                        routine.get("studio") or "",
                        routine["event"],
                    )

            except Exception as e:
                print(f"❌ Routine failed: {e}")

            finally:
                self._trigger_source = "click"

            self.routine_store.mark_run(
                routine["id"],
                datetime.date.today(),
            )

            if self.tray is not None:
                self.tray.showMessage(
                    "LensFlow routine",
                    f"Done: {routine['kind'].replace('studio', 'opened')} "
                    f"{routine['target']} ({routine['time']})",
                    QSystemTrayIcon.MessageIcon.Information,
                    3000,
                )

        if self.stack.currentWidget() is self.activity_page:
            self.activity_page.refresh()

        if self.stack.currentWidget() is self.notifications_page:
            self.notifications_page.refresh()

    # =============================================================
    # SYSTEM TRAY
    # =============================================================

    def _setup_tray(self):

        self._quitting = False
        self._told_about_tray = False
        self.tray = None

        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        self.tray = QSystemTrayIcon(_app_icon(), self)
        self.tray.setToolTip("LensFlow")

        menu = QMenu(self)

        open_action = QAction("Open LensFlow", self)
        open_action.triggered.connect(self.show_from_tray)
        menu.addAction(open_action)

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_app)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)

        self.tray.activated.connect(
            lambda reason: self.show_from_tray()
            if reason == QSystemTrayIcon.ActivationReason.Trigger
            else None
        )

        self.tray.show()

    def show_from_tray(self):

        self.showNormal()
        self.raise_()
        self.activateWindow()

    def restart_app(self):
        """Start a fresh LensFlow (themes apply at startup), then quit."""

        args = [a for a in sys.argv if a != "--background"]

        if getattr(sys, "frozen", False):
            QProcess.startDetached(sys.executable, args[1:])
        else:
            QProcess.startDetached(sys.executable, args)

        self.quit_app()

    def quit_app(self):

        self._quitting = True
        self.close()



# =============================================================
# STYLESHEET
# =============================================================

def _load_stylesheet(
    app
):

    # theme.qss mapped to the theme chosen in Settings.
    app.setStyleSheet(
        global_stylesheet()
    )


# =============================================================
# APP ICON
# =============================================================

def _app_icon():
    """A simple lens mark, drawn in code (no image files needed)."""

    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(PRIMARY))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(4, 4, 56, 56, 16, 16)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(QPen(QColor("#0A0A0D"), 5))
    painter.drawEllipse(17, 17, 30, 30)
    painter.setBrush(QColor("#0A0A0D"))
    painter.drawEllipse(28, 28, 8, 8)
    painter.end()

    return QIcon(pixmap)


# =============================================================
# MAIN
# =============================================================

def main():

    if "--self-test" in sys.argv:
        from backend.self_test import run
        sys.exit(run())

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

    # Closing the window may only hide it (tray); quit explicitly instead.
    app.setQuitOnLastWindowClosed(False)

    app.setWindowIcon(_app_icon())

    window = MainWindow()

    if "--background" in sys.argv and window.tray is not None:
        # Started at sign-in: stay in the tray until the user opens it.
        pass
    else:
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
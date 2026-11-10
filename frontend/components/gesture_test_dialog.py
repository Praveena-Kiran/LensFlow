"""
Live gesture tester.

Shows what Wield sees in real time, using the same rules as a running
studio: custom gestures are checked first, then the built-in ones, and the
GestureStabilizer decides when a gesture actually *triggers*. Nothing is
executed — it's safe to try gestures here.
"""

import time

from PySide6.QtCore import QThread, Qt, Slot
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from frontend.components.gesture_recorder_dialog import (
    PREVIEW_HEIGHT,
    PREVIEW_WIDTH,
    CameraPreviewWorker,
)
from frontend.styles.theme import (
    BG_DARK,
    BORDER,
    ERROR,
    PRIMARY,
    PRIMARY_TEXT,
    SECONDARY_TEXT,
    SUCCESS,
    SURFACE,
    SURFACE_ACTIVE,
    SURFACE_HOVER,
    TEXT_MUTED,
    WARNING,
)
from backend.gestures.custom_gestures import CustomGestureMatcher, CustomGestureStore
from backend.gestures.gesture_stabilizer import GestureStabilizer
from backend.gestures.motions import MotionRecognizer
from backend.app_info import APP_NAME


MAX_LOG_ENTRIES = 5


class GestureTestDialog(QDialog):

    def __init__(self, gesture_map=None, store=None, parent=None):

        super().__init__(parent)

        # gesture name -> action, used to show what a trigger would do
        self.gesture_map = gesture_map or {}

        store = store or CustomGestureStore()
        self.matcher = CustomGestureMatcher(store.gestures)
        self.stabilizer = GestureStabilizer()

        self.motions = MotionRecognizer()
        self._motion_shown_until = 0.0

        self.log = []

        self.thread = None
        self.worker = None

        self.setWindowTitle("Test Gestures")
        self.setModal(True)
        self.setMinimumWidth(560)

        self._build_ui()
        self._start_camera()

    # -----------------------------------------------------
    # UI
    # -----------------------------------------------------

    def _build_ui(self):

        self.setStyleSheet(f"""
            QDialog {{ background: {BG_DARK}; }}
            QLabel {{ color: {PRIMARY_TEXT}; font-size: 14px; }}
            QPushButton {{
                background: {SURFACE_HOVER}; color: {PRIMARY_TEXT};
                border: 1px solid {BORDER}; border-radius: 10px;
                padding: 10px 18px; font-size: 14px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {SURFACE_ACTIVE}; }}
            QProgressBar {{
                background: {SURFACE}; border: none; border-radius: 4px;
                height: 8px;
            }}
            QProgressBar::chunk {{ background: {PRIMARY}; border-radius: 4px; }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Test your gestures")
        title.setStyleSheet(
            f"color: {PRIMARY_TEXT}; font-size: 20px; font-weight: 700;"
        )
        layout.addWidget(title)

        intro = QLabel(
            f"Make a gesture to see what {APP_NAME} recognises. "
            "Nothing runs here, so it's safe to experiment."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet(f"color: {SECONDARY_TEXT}; font-size: 14px;")
        layout.addWidget(intro)

        self.preview = QLabel("Starting camera…")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setFixedSize(PREVIEW_WIDTH, PREVIEW_HEIGHT)
        self.preview.setStyleSheet(
            f"background: {SURFACE}; border: 1px solid {BORDER}; "
            f"border-radius: 14px; color: {TEXT_MUTED};"
        )
        layout.addWidget(self.preview, 0, Qt.AlignHCenter)

        self.seeing = QLabel("—")
        self.seeing.setAlignment(Qt.AlignCenter)
        self.seeing.setAccessibleName("Recognised gesture")
        self.seeing.setStyleSheet(
            f"color: {PRIMARY_TEXT}; font-size: 22px; font-weight: 700;"
        )
        layout.addWidget(self.seeing)

        self.confidence = QProgressBar()
        self.confidence.setRange(0, 100)
        self.confidence.setTextVisible(False)
        layout.addWidget(self.confidence)

        self.detail = QLabel("")
        self.detail.setAlignment(Qt.AlignCenter)
        self.detail.setStyleSheet(f"color: {SECONDARY_TEXT}; font-size: 13px;")
        layout.addWidget(self.detail)

        log_title = QLabel("Triggered")
        log_title.setStyleSheet(
            f"color: {SECONDARY_TEXT}; font-size: 13px; font-weight: 600; "
            "margin-top: 6px;"
        )
        layout.addWidget(log_title)

        self.log_label = QLabel("Nothing yet")
        self.log_label.setWordWrap(True)
        self.log_label.setAccessibleName("Triggered gestures")
        self.log_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px;")
        layout.addWidget(self.log_label)

        buttons = QHBoxLayout()
        buttons.addStretch()

        close_button = QPushButton("Done")
        close_button.clicked.connect(self.accept)
        buttons.addWidget(close_button)

        layout.addLayout(buttons)

    # -----------------------------------------------------
    # CAMERA
    # -----------------------------------------------------

    def _start_camera(self):

        self.thread = QThread(self)
        self.worker = CameraPreviewWorker()
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.frame_ready.connect(self._on_frame)
        self.worker.hand_sample.connect(self._on_hand_sample)
        self.worker.error.connect(self._on_camera_error)
        self.worker.finished.connect(self.thread.quit)

        self.thread.start()

    def _stop_camera(self):

        if self.worker is not None:
            self.worker.stop()

        if self.thread is not None:
            self.thread.quit()
            self.thread.wait(3000)

        self.worker = None
        self.thread = None

    # -----------------------------------------------------
    # RECOGNITION (same order as GestureWorker)
    # -----------------------------------------------------

    def classify(self, vector, builtin, builtin_confidence):
        """Return (gesture, confidence, kind) for one frame."""

        if vector is None:
            return None, 0.0, None

        name, confidence = self.matcher.match_vector(vector)

        if name:
            return name, confidence, "custom"

        if builtin:
            return builtin, builtin_confidence, "built-in"

        return None, 0.0, None

    @Slot(QImage, object, object, float)
    def _on_frame(self, image, vector, builtin, builtin_confidence):

        self.preview.setPixmap(
            QPixmap.fromImage(image).scaled(
                PREVIEW_WIDTH,
                PREVIEW_HEIGHT,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

        if self.motions.active or time.monotonic() < self._motion_shown_until:
            # Mid-movement (same rule as a running studio: poses paused), or
            # a motion was just recognised and is still on screen.
            self.stabilizer.update(None, 0.0)
            return

        gesture, confidence, kind = self.classify(
            vector, builtin, builtin_confidence
        )

        self.confidence.setValue(int(confidence * 100))

        if vector is None:
            self.seeing.setText("No hand in view")
            self.seeing.setStyleSheet(
                f"color: {WARNING}; font-size: 22px; font-weight: 700;"
            )
            self.detail.setText("")
        elif gesture is None:
            self.seeing.setText("Hand seen, no gesture")
            self.seeing.setStyleSheet(
                f"color: {TEXT_MUTED}; font-size: 22px; font-weight: 700;"
            )
            self.detail.setText(self._closest_hint(vector))
        else:
            self.seeing.setText(gesture)
            self.seeing.setStyleSheet(
                f"color: {PRIMARY_TEXT}; font-size: 22px; font-weight: 700;"
            )
            action = self.gesture_map.get(gesture)
            suffix = f"  ·  would run: {action}" if action else ""
            self.detail.setText(f"{kind} · {int(confidence * 100)}%{suffix}")

        triggered = self.stabilizer.update(gesture, confidence)

        if triggered:
            self._add_log(triggered)

    @Slot(float, object)
    def _on_hand_sample(self, t, sample):

        result = self.motions.update(t, sample)

        if result:
            motion, confidence = result
            self._motion_shown_until = time.monotonic() + 1.5
            self.seeing.setText(motion)
            action = self.gesture_map.get(motion)
            suffix = f"  ·  would run: {action}" if action else ""
            self.detail.setText(f"motion · {int(confidence * 100)}%{suffix}")
            self._add_log(motion)

    def _closest_hint(self, vector):
        """Explain near-misses so users know whether to re-record."""

        if not self.matcher.has_gestures():
            return ""

        name, distance = self.matcher.closest(vector)[0]

        if distance <= self.matcher.max_distance * 1.5:
            return f'Close to "{name}". Try matching your recorded pose.'

        return ""

    def _add_log(self, gesture):

        stamp = time.strftime("%H:%M:%S")
        action = self.gesture_map.get(gesture)
        entry = f"{stamp}   {gesture}" + (f"  →  {action}" if action else "")

        self.log.insert(0, entry)
        del self.log[MAX_LOG_ENTRIES:]

        self.log_label.setText("\n".join(self.log))
        self.log_label.setStyleSheet(f"color: {SUCCESS}; font-size: 13px;")

    @Slot(str)
    def _on_camera_error(self, message):
        self.worker = None
        self.preview.setText("Camera unavailable")
        self.seeing.setText(message)
        self.seeing.setWordWrap(True)
        self.seeing.setStyleSheet(f"color: {ERROR}; font-size: 14px;")

    def done(self, result):
        self._stop_camera()
        super().done(result)

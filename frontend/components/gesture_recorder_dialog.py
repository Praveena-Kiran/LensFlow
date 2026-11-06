"""
Record a custom gesture from the webcam.

Flow for the user:
    1. Type a name.
    2. Press "Record". A short countdown gives them time to get into the pose,
       then LensFlow captures the hand for a couple of seconds.
    3. Repeat for TAKES_REQUIRED takes (small variations make recognition
       more forgiving).
    4. LensFlow checks the recording (enough frames, not a built-in pose,
       not too close to another custom gesture) and the user saves it.

The camera runs on a background thread (CameraPreviewWorker) so the dialog
stays responsive. Only one thing can use the webcam at a time, so a studio
that is already running must be stopped first.
"""

import time

import cv2

from PySide6.QtCore import QObject, QThread, QTimer, Qt, Signal, Slot
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from frontend.styles.theme import (
    BG_DARK,
    BORDER,
    ERROR,
    PRIMARY,
    PRIMARY_HOVER,
    PRIMARY_MUTED,
    PRIMARY_PRESSED,
    PRIMARY_TEXT,
    SECONDARY_TEXT,
    SUCCESS,
    SURFACE,
    SURFACE_ACTIVE,
    SURFACE_HOVER,
    TEXT_DISABLED,
    TEXT_MUTED,
    WARNING,
)
from backend.gestures.motions import palm_point
from backend.gestures.custom_gestures import (
    CustomGestureStore,
    normalize_landmarks,
    review_recording,
)


TAKES_REQUIRED = 3
COUNTDOWN_SECONDS = 3
CAPTURE_MS = 2000

# A frame counts as "looks like a built-in gesture" above this confidence.
BUILTIN_CONFIDENCE = 0.6

PREVIEW_WIDTH = 480
PREVIEW_HEIGHT = 360

# Pairs of landmark indices to draw the hand skeleton on the preview.
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
]


# =========================================================
# CAMERA WORKER
# =========================================================

class CameraPreviewWorker(QObject):

    # QImage for the preview, normalised pose (or None),
    # built-in gesture name (or None), built-in confidence
    frame_ready = Signal(QImage, object, object, float)

    # Time (monotonic seconds) and palm sample (x, y, size) or None, for
    # motion gestures. Emitted just before frame_ready.
    hand_sample = Signal(float, object)
    error = Signal(str)
    finished = Signal()

    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self.running = False

    @Slot()
    def run(self):

        # Imported here so the dialog can open instantly and so a missing
        # model shows as an error message rather than a crash.
        try:
            from backend.gestures.google_gesture_recognizer import (
                GoogleGestureRecognizer,
            )
            recognizer = GoogleGestureRecognizer()
        except Exception as e:
            self.error.emit(f"Could not load the gesture model:\n{e}")
            self.finished.emit()
            return

        camera = cv2.VideoCapture(self.camera_index)

        if not camera.isOpened():
            self.error.emit(
                "Could not open the webcam.\n\n"
                "If a studio is running, stop it first, then try again."
            )
            self.finished.emit()
            return

        self.running = True

        while self.running:

            ok, frame = camera.read()

            if not ok:
                self.error.emit("Could not read from the webcam.")
                break

            frame = cv2.flip(frame, 1)

            builtin, confidence = recognizer.detect(frame)

            h, w = frame.shape[:2]

            self.hand_sample.emit(
                time.monotonic(),
                palm_point(recognizer.last_image_landmarks, w / h),
            )

            vector = normalize_landmarks(
                recognizer.last_landmarks,
                recognizer.last_handedness,
            )

            if recognizer.last_image_landmarks is not None:
                draw_hand(frame, recognizer.last_image_landmarks)

            if confidence < BUILTIN_CONFIDENCE:
                builtin = None

            self.frame_ready.emit(
                to_qimage(frame), vector, builtin, float(confidence or 0.0)
            )

        camera.release()
        self.finished.emit()

    @Slot()
    def stop(self):
        self.running = False


def draw_hand(frame, landmarks):

    h, w = frame.shape[:2]
    points = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]

    for a, b in HAND_CONNECTIONS:
        cv2.line(frame, points[a], points[b], (255, 92, 124), 2, cv2.LINE_AA)  # brand violet, in BGR

    for p in points:
        cv2.circle(frame, p, 4, (255, 255, 255), -1, cv2.LINE_AA)


def to_qimage(frame):

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, _ = rgb.shape

    # .copy() detaches the image from the numpy buffer before it crosses threads.
    return QImage(rgb.data, w, h, 3 * w, QImage.Format_RGB888).copy()


# =========================================================
# DIALOG
# =========================================================

class GestureRecorderDialog(QDialog):

    def __init__(self, builtin_names, store=None, parent=None):

        super().__init__(parent)

        self.builtin_names = list(builtin_names)
        self.store = store or CustomGestureStore()

        self.samples = []
        self.take_samples = []
        self.builtin_hits = 0
        self.takes_done = 0

        self.state = "idle"        # idle | countdown | capturing | review
        self.countdown_left = 0
        self.saved_name = None

        self.thread = None
        self.worker = None

        self.setWindowTitle("Record Custom Gesture")
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
            QLineEdit {{
                background: {SURFACE}; color: {PRIMARY_TEXT};
                border: 1px solid {BORDER}; border-radius: 10px;
                padding: 10px 12px; font-size: 15px;
            }}
            QLineEdit:focus {{ border-color: {PRIMARY}; }}
            QPushButton {{
                background: {SURFACE_HOVER}; color: {PRIMARY_TEXT}; border: 1px solid {BORDER};
                border-radius: 10px; padding: 10px 18px;
                font-size: 14px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {SURFACE_ACTIVE}; }}
            QPushButton:disabled {{ background: {SURFACE}; color: {TEXT_DISABLED}; }}
            QPushButton#Primary {{ background: {PRIMARY}; border: none; color: white; }}
            QPushButton#Primary:hover {{ background: {PRIMARY_HOVER}; }}
            QPushButton#Primary:pressed {{ background: {PRIMARY_PRESSED}; }}
            QPushButton#Primary:disabled {{ background: {PRIMARY_MUTED}; color: {TEXT_MUTED}; }}
            QProgressBar {{
                background: {SURFACE}; border: none; border-radius: 4px;
                height: 8px; text-align: center;
            }}
            QProgressBar::chunk {{ background: {PRIMARY}; border-radius: 4px; }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel("Teach LensFlow a new gesture")
        title.setStyleSheet(f"color: {PRIMARY_TEXT}; font-size: 20px; font-weight: 700;")
        layout.addWidget(title)

        intro = QLabel(
            "Use any hand pose that's comfortable for you. "
            f"You'll hold it for {CAPTURE_MS // 1000} seconds, "
            f"{TAKES_REQUIRED} times."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet(f"color: {SECONDARY_TEXT}; font-size: 14px;")
        layout.addWidget(intro)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Gesture name, e.g. Two-finger pinch")
        self.name_input.setAccessibleName("Gesture name")
        self.name_input.textChanged.connect(self._update_buttons)
        layout.addWidget(self.name_input)

        self.preview = QLabel("Starting camera…")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setFixedSize(PREVIEW_WIDTH, PREVIEW_HEIGHT)
        self.preview.setStyleSheet(
            f"background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 14px; color: {TEXT_MUTED};"
        )
        layout.addWidget(self.preview, 0, Qt.AlignHCenter)

        self.hand_status = QLabel("")
        self.hand_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.hand_status)

        self.status = QLabel("")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setWordWrap(True)
        self.status.setStyleSheet(f"color: {PRIMARY_TEXT}; font-size: 16px; font-weight: 600;")
        self.status.setAccessibleName("Recording status")
        layout.addWidget(self.status)

        self.progress = QProgressBar()
        self.progress.setRange(0, TAKES_REQUIRED)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress)

        buttons = QHBoxLayout()

        self.reset_button = QPushButton("Start over")
        self.reset_button.clicked.connect(self._reset)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        self.record_button = QPushButton("Record take 1")
        self.record_button.setObjectName("Primary")
        self.record_button.clicked.connect(self._start_take)

        self.save_button = QPushButton("Save gesture")
        self.save_button.setObjectName("Primary")
        self.save_button.clicked.connect(self._save)

        buttons.addWidget(self.reset_button)
        buttons.addStretch()
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.record_button)
        buttons.addWidget(self.save_button)
        layout.addLayout(buttons)

        self.countdown_timer = QTimer(self)
        self.countdown_timer.setInterval(1000)
        self.countdown_timer.timeout.connect(self._tick_countdown)

        self.capture_timer = QTimer(self)
        self.capture_timer.setSingleShot(True)
        self.capture_timer.timeout.connect(self._finish_take)

        self._set_status("Type a name, then press Record.")
        self._update_buttons()

    def _set_status(self, text, color=PRIMARY_TEXT):
        self.status.setText(text)
        self.status.setStyleSheet(
            f"color: {color}; font-size: 16px; font-weight: 600;"
        )

    def _update_buttons(self):

        busy = self.state in ("countdown", "capturing")
        has_name = bool(self.name_input.text().strip())

        self.name_input.setEnabled(not busy and self.takes_done == 0)
        self.record_button.setVisible(self.state != "review")
        self.record_button.setEnabled(
            has_name and not busy and self.worker is not None
        )
        self.record_button.setText(f"Record take {self.takes_done + 1}")
        self.save_button.setVisible(self.state == "review")
        self.reset_button.setEnabled(not busy and self.takes_done > 0)

    # -----------------------------------------------------
    # CAMERA
    # -----------------------------------------------------

    def _start_camera(self):

        self.thread = QThread(self)
        self.worker = CameraPreviewWorker()
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.frame_ready.connect(self._on_frame)
        self.worker.error.connect(self._on_camera_error)
        self.worker.finished.connect(self.thread.quit)

        self.thread.start()

    def _stop_camera(self):

        if self.worker is not None:
            # Called directly (not via a queued signal) because the worker's
            # thread is busy in its capture loop; setting the flag is enough.
            self.worker.stop()

        if self.thread is not None:
            self.thread.quit()
            self.thread.wait(3000)

        self.worker = None
        self.thread = None

    @Slot(QImage, object, object, float)
    def _on_frame(self, image, vector, builtin, builtin_confidence=0.0):

        self.preview.setPixmap(
            QPixmap.fromImage(image).scaled(
                PREVIEW_WIDTH,
                PREVIEW_HEIGHT,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

        if vector is None:
            self.hand_status.setText("No hand in view")
            self.hand_status.setStyleSheet(f"color: {WARNING}; font-size: 13px;")
        else:
            self.hand_status.setText("Hand detected")
            self.hand_status.setStyleSheet(f"color: {SUCCESS}; font-size: 13px;")

        if self.state == "capturing" and vector is not None:
            self.take_samples.append(vector)
            if builtin:
                self.builtin_hits += 1

    @Slot(str)
    def _on_camera_error(self, message):
        self.worker = None
        self.preview.setText("Camera unavailable")
        self._set_status(message, ERROR)
        self._update_buttons()

    # -----------------------------------------------------
    # RECORDING
    # -----------------------------------------------------

    def _start_take(self):

        self.state = "countdown"
        self.countdown_left = COUNTDOWN_SECONDS
        self._set_status(f"Get into your pose… {self.countdown_left}")
        self.countdown_timer.start()
        self._update_buttons()

    def _tick_countdown(self):

        self.countdown_left -= 1

        if self.countdown_left > 0:
            self._set_status(f"Get into your pose… {self.countdown_left}")
            return

        self.countdown_timer.stop()
        self.state = "capturing"
        self.take_samples = []
        self._set_status("Hold it…", PRIMARY_HOVER)
        self.capture_timer.start(CAPTURE_MS)
        self._update_buttons()

    def _finish_take(self):

        if len(self.take_samples) < 5:
            self.state = "idle"
            self._set_status(
                "Your hand wasn't visible. Keep your whole hand in view "
                "and try that take again.",
                WARNING,
            )
            self._update_buttons()
            return

        self.samples.extend(self.take_samples)
        self.takes_done += 1
        self.progress.setValue(self.takes_done)

        if self.takes_done < TAKES_REQUIRED:
            self.state = "idle"
            self._set_status(
                f"Take {self.takes_done} done. Relax, then record the next one."
            )
            self._update_buttons()
            return

        self._review()

    def _review(self):

        ok, message = review_recording(
            self.name_input.text(),
            self.samples,
            self.builtin_hits,
            self.store.gestures,
            self.builtin_names,
        )

        if ok:
            self.state = "review"
            name = self.name_input.text().strip()
            note = (
                f'Ready to save "{name}".'
                if self.store.get(name) is None
                else f'Ready to save. This replaces your existing "{name}".'
            )
            self._set_status(note, SUCCESS)
        else:
            self.state = "idle"
            self._set_status(message, ERROR)
            self.record_button.setEnabled(False)

        self._update_buttons()

        if not ok:
            # Nothing more to record; the user needs to start over.
            self.record_button.setVisible(False)

    def _reset(self):

        self.samples = []
        self.take_samples = []
        self.builtin_hits = 0
        self.takes_done = 0
        self.state = "idle"
        self.progress.setValue(0)
        self._set_status("Type a name, then press Record.")
        self._update_buttons()

    def _save(self):

        name = self.name_input.text().strip()
        self.store.add(name, self.samples)
        self.saved_name = name
        self.accept()

    # -----------------------------------------------------
    # CLEANUP
    # -----------------------------------------------------

    def done(self, result):
        self.countdown_timer.stop()
        self.capture_timer.stop()
        self._stop_camera()
        super().done(result)

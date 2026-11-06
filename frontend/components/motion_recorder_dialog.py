"""
Record a custom motion (e.g. a wave or a circle) from the webcam.

Each take: a short countdown, then the user makes the movement once within
TAKE_WINDOW_MS. MotionSegmenter finds the stroke; after TAKES_REQUIRED
takes, review_motion() checks the takes agree and don't look like a swipe
or another motion, and the user saves it.
"""

from PySide6.QtCore import QThread, QTimer, Qt, Slot
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

from frontend.components.gesture_recorder_dialog import (
    PREVIEW_HEIGHT,
    PREVIEW_WIDTH,
    CameraPreviewWorker,
)
from frontend.styles.theme import (
    ON_PRIMARY,
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
from backend.gestures.motions import (
    MotionSegmenter,
    MotionStore,
    normalize_trajectory,
    review_motion,
)


TAKES_REQUIRED = 3
COUNTDOWN_SECONDS = 3
TAKE_WINDOW_MS = 3000


class MotionRecorderDialog(QDialog):

    def __init__(self, taken_names=(), store=None, parent=None):

        super().__init__(parent)

        self.taken_names = list(taken_names)
        self.store = store or MotionStore()

        self.samples = []
        self.state = "idle"        # idle | countdown | capturing | review
        self.countdown_left = 0
        self.saved_name = None
        self.segmenter = MotionSegmenter()

        self.thread = None
        self.worker = None

        self.setWindowTitle("Record Custom Motion")
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
                background: {SURFACE_HOVER}; color: {PRIMARY_TEXT};
                border: 1px solid {BORDER}; border-radius: 10px;
                padding: 10px 18px; font-size: 14px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {SURFACE_ACTIVE}; }}
            QPushButton:disabled {{ background: {SURFACE}; color: {TEXT_DISABLED}; }}
            QPushButton#Primary {{ background: {PRIMARY}; border: none; color: {ON_PRIMARY}; }}
            QPushButton#Primary:hover {{ background: {PRIMARY_HOVER}; }}
            QPushButton#Primary:pressed {{ background: {PRIMARY_PRESSED}; }}
            QPushButton#Primary:disabled {{ background: {PRIMARY_MUTED}; color: {TEXT_MUTED}; }}
            QProgressBar {{
                background: {SURFACE}; border: none; border-radius: 4px; height: 8px;
            }}
            QProgressBar::chunk {{ background: {PRIMARY}; border-radius: 4px; }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel("Teach LensFlow a movement")
        title.setStyleSheet(f"color: {PRIMARY_TEXT}; font-size: 20px; font-weight: 700;")
        layout.addWidget(title)

        intro = QLabel(
            "Make one smooth movement, like a wave or a circle, then hold "
            f"still. You'll do it {TAKES_REQUIRED} times. Straight swipes "
            "are already built in."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet(f"color: {SECONDARY_TEXT}; font-size: 14px;")
        layout.addWidget(intro)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Motion name, e.g. Wave")
        self.name_input.setAccessibleName("Motion name")
        self.name_input.textChanged.connect(self._update_buttons)
        layout.addWidget(self.name_input)

        self.preview = QLabel("Starting camera…")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setFixedSize(PREVIEW_WIDTH, PREVIEW_HEIGHT)
        self.preview.setStyleSheet(
            f"background: {SURFACE}; border: 1px solid {BORDER}; "
            f"border-radius: 14px; color: {TEXT_MUTED};"
        )
        layout.addWidget(self.preview, 0, Qt.AlignHCenter)

        self.status = QLabel("")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setWordWrap(True)
        self.status.setAccessibleName("Recording status")
        layout.addWidget(self.status)

        self.progress = QProgressBar()
        self.progress.setRange(0, TAKES_REQUIRED)
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

        self.save_button = QPushButton("Save motion")
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

        self.window_timer = QTimer(self)
        self.window_timer.setSingleShot(True)
        self.window_timer.timeout.connect(self._take_timed_out)

        self._set_status("Type a name, then press Record.")
        self._update_buttons()

    def _set_status(self, text, color=PRIMARY_TEXT):
        self.status.setText(text)
        self.status.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: 600;")

    def _update_buttons(self):

        busy = self.state in ("countdown", "capturing")
        takes = len(self.samples)

        self.name_input.setEnabled(not busy and takes == 0)
        self.record_button.setVisible(self.state != "review")
        self.record_button.setEnabled(
            bool(self.name_input.text().strip()) and not busy
            and self.worker is not None and takes < TAKES_REQUIRED
        )
        self.record_button.setText(f"Record take {takes + 1}")
        self.save_button.setVisible(self.state == "review")
        self.reset_button.setEnabled(not busy and takes > 0)

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

    @Slot(QImage, object, object, float)
    def _on_frame(self, image, vector, builtin, builtin_confidence):

        self.preview.setPixmap(
            QPixmap.fromImage(image).scaled(
                PREVIEW_WIDTH, PREVIEW_HEIGHT,
                Qt.KeepAspectRatio, Qt.SmoothTransformation,
            )
        )

    @Slot(float, object)
    def _on_hand_sample(self, t, sample):

        if self.state != "capturing":
            return

        stroke = self.segmenter.update(t, sample)

        if stroke:
            self._finish_take(stroke)

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
        self._set_status(f"Get ready… {self.countdown_left}")
        self.countdown_timer.start()
        self._update_buttons()

    def _tick_countdown(self):

        self.countdown_left -= 1

        if self.countdown_left > 0:
            self._set_status(f"Get ready… {self.countdown_left}")
            return

        self.countdown_timer.stop()
        self.segmenter.reset()
        self.state = "capturing"
        self._set_status("Go! Make your movement, then hold still.", PRIMARY_HOVER)
        self.window_timer.start(TAKE_WINDOW_MS)
        self._update_buttons()

    def _take_timed_out(self):

        if self.state != "capturing":
            return

        # The hand may still be mid-movement; end the stroke if there is one.
        stroke = self.segmenter.update(0.0, None)

        if stroke:
            self._finish_take(stroke)
            return

        self.state = "idle"
        self._set_status(
            "LensFlow didn't see a movement. Keep your hand in view and "
            "move a bit further or faster.",
            WARNING,
        )
        self._update_buttons()

    def _finish_take(self, stroke):

        self.window_timer.stop()

        trajectory = normalize_trajectory(stroke["points"])

        if trajectory is None:
            self._take_timed_out()
            return

        self.samples.append(trajectory)
        self.progress.setValue(len(self.samples))

        if len(self.samples) < TAKES_REQUIRED:
            self.state = "idle"
            self._set_status(f"Take {len(self.samples)} done. Record the next one.")
            self._update_buttons()
            return

        ok, message = review_motion(
            self.name_input.text(),
            self.samples,
            self.store.motions,
            self.taken_names,
        )

        if ok:
            self.state = "review"
            self._set_status(f'Ready to save "{self.name_input.text().strip()}".', SUCCESS)
        else:
            self.state = "idle"
            self._set_status(message, ERROR)

        self._update_buttons()

    def _reset(self):
        self.samples = []
        self.state = "idle"
        self.progress.setValue(0)
        self._set_status("Type a name, then press Record.")
        self._update_buttons()

    def _save(self):
        name = self.name_input.text().strip()
        self.store.add(name, self.samples)
        self.saved_name = name
        self.accept()

    def done(self, result):
        self.countdown_timer.stop()
        self.window_timer.stop()
        self._stop_camera()
        super().done(result)

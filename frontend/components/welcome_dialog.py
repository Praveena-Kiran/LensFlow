"""
The first-run welcome: four short steps, each skippable.

    1. Hi           - what the app is, and the user's name
    2. Your look    - theme (applied by restarting once at the end)
    3. Camera       - live preview; confirms a hand can be seen
    4. Try it       - make a thumbs up, then a few tips

Shown once (settings key "onboarded"), and again from Settings → About.
"""

from PySide6.QtCore import QRectF, QThread, Qt, Slot
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

import os

from frontend.components.gesture_recorder_dialog import CameraPreviewWorker
from frontend.styles import theme as theme_module
from frontend.styles.theme import (
    BG_DARK,
    BORDER,
    ON_PRIMARY,
    OVERLAY_1,
    OVERLAY_2,
    PRIMARY,
    PRIMARY_HOVER,
    PRIMARY_TEXT,
    SECONDARY_TEXT,
    SUCCESS,
    SURFACE,
    TEXT_MUTED,
    WARNING,
)
from backend.app_info import APP_NAME
from backend.paths import APP_DIR
from backend.settings.settings_manager import SettingsManager
from backend.settings.user import display_name, set_display_name


ONBOARDED_KEY = "onboarded"
THUMBS_UP = "👍 Thumbs Up"
PREVIEW_W, PREVIEW_H = 400, 260


def needs_welcome():
    if os.environ.get("WIELD_NO_WELCOME"):
        return False  # automated tests
    try:
        return not SettingsManager().get_setting(ONBOARDED_KEY)
    except Exception:
        return False


def mark_welcomed():
    SettingsManager().set_setting(ONBOARDED_KEY, True)


def _label(text, color=PRIMARY_TEXT, size=14, weight=400, wrap=True, center=False):
    label = QLabel(text)
    label.setWordWrap(wrap)
    if center:
        label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet(
        f"color: {color}; font-size: {size}px; font-weight: {weight}; "
        "background: transparent; border: none;"
    )
    return label


class WelcomeDialog(QDialog):

    STEPS = 4

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setWindowTitle(f"Welcome to {APP_NAME}")
        self.setModal(True)
        self.setFixedSize(620, 600)
        self.setStyleSheet(f"""
            QDialog {{ background: {BG_DARK}; }}
            QLineEdit {{
                background: {SURFACE}; color: {PRIMARY_TEXT};
                border: 1px solid {BORDER}; border-radius: 10px;
                padding: 10px 12px; font-size: 15px;
            }}
            QLineEdit:focus {{ border: 1px solid {PRIMARY}; }}
        """)

        self.chosen_theme = theme_module.THEME_NAME
        self.saw_hand = False
        self.did_gesture = False

        self.thread = None
        self.worker = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 26)
        layout.setSpacing(18)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._page_hi())
        self.pages.addWidget(self._page_theme())
        self.pages.addWidget(self._page_camera())
        self.pages.addWidget(self._page_try())
        layout.addWidget(self.pages, 1)

        # Step dots + buttons -----------------------------------------
        bottom = QHBoxLayout()

        self.dots = QLabel()
        self.dots.setStyleSheet("background: transparent;")
        bottom.addWidget(self.dots)
        bottom.addStretch()

        self.skip_button = self._button("Skip", quiet=True)
        self.skip_button.setToolTip("Skip the welcome. You can see it again in Settings → About.")
        self.skip_button.clicked.connect(self.finish)

        self.back_button = self._button("Back")
        self.back_button.clicked.connect(lambda: self.go(self.pages.currentIndex() - 1))

        self.next_button = self._button("Continue", primary=True)
        self.next_button.setDefault(True)
        self.next_button.clicked.connect(self._next)

        bottom.addWidget(self.skip_button)
        bottom.addWidget(self.back_button)
        bottom.addWidget(self.next_button)
        layout.addLayout(bottom)

        self.go(0)

    # -----------------------------------------------------
    # PAGES
    # -----------------------------------------------------

    def _page(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        return page, layout

    def _page_hi(self):

        page, layout = self._page()
        layout.addStretch()

        icon = QLabel()
        path = os.path.join(APP_DIR, "assets", "icons", "wield.png")
        if os.path.isfile(path):
            icon.setPixmap(QPixmap(path).scaled(84, 84, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("background: transparent;")
        layout.addWidget(icon)

        layout.addSpacing(6)
        layout.addWidget(_label(f"Welcome to {APP_NAME}", PRIMARY_TEXT, 28, 700, center=True))
        layout.addWidget(_label(
            "Control your computer with your hands: gestures, swipes and "
            "moves you choose. Everything runs on this computer.",
            SECONDARY_TEXT, 15, center=True,
        ))

        layout.addSpacing(24)
        layout.addWidget(_label("What should we call you?", PRIMARY_TEXT, 14, 600))

        self.name_input = QLineEdit(display_name())
        self.name_input.setPlaceholderText("Your name")
        self.name_input.setAccessibleName("Your name")
        self.name_input.setMaxLength(40)
        self.name_input.returnPressed.connect(self._next)
        layout.addWidget(self.name_input)

        layout.addStretch()
        return page

    def _page_theme(self):

        page, layout = self._page()

        layout.addWidget(_label("Pick a look", PRIMARY_TEXT, 24, 700))
        layout.addWidget(_label(
            "You can change it any time in Settings.", SECONDARY_TEXT, 14,
        ))
        layout.addSpacing(10)

        grid = QHBoxLayout()
        grid.setSpacing(12)
        self.theme_group = QButtonGroup(self)

        for name, palette in theme_module.THEMES.items():

            button = QPushButton(palette["label"])
            button.setCheckable(True)
            button.setChecked(name == self.chosen_theme)
            button.setCursor(Qt.PointingHandCursor)
            button.setAccessibleName(f"{palette['label']} theme")
            button.setFixedSize(124, 150)
            button.setStyleSheet(f"""
                QPushButton {{
                    background: {palette['BG_DARK']}; color: {palette['PRIMARY_TEXT']};
                    border: 2px solid {palette['BORDER']}; border-radius: 16px;
                    font-size: 14px; font-weight: 600; padding-top: 70px;
                }}
                QPushButton:hover {{ border: 2px solid {palette['PRIMARY_HOVER']}; }}
                QPushButton:checked {{ border: 3px solid {palette['PRIMARY']}; }}
            """)

            # A mini window in the theme's colours.
            card = QLabel(button)
            card.setGeometry(14, 14, 92, 52)
            card.setStyleSheet(
                f"background: {palette['SURFACE']}; border: 1px solid {palette['BORDER']}; border-radius: 9px;"
            )
            dot = QLabel(button)
            dot.setGeometry(24, 24, 16, 16)
            dot.setStyleSheet(f"background: {palette['PRIMARY']}; border-radius: 8px; border: none;")
            line = QLabel(button)
            line.setGeometry(24, 48, 60, 6)
            line.setStyleSheet(f"background: {palette['SECONDARY_TEXT']}; border-radius: 3px; border: none;")

            button.clicked.connect(lambda checked=False, n=name: self._pick_theme(n))
            self.theme_group.addButton(button)
            grid.addWidget(button)

        layout.addLayout(grid)

        layout.addSpacing(8)
        self.theme_note = _label("", TEXT_MUTED, 13)
        layout.addWidget(self.theme_note)
        layout.addStretch()
        return page

    def _preview(self):
        preview = QLabel("Starting camera…")
        preview.setAlignment(Qt.AlignCenter)
        preview.setFixedSize(PREVIEW_W, PREVIEW_H)
        preview.setStyleSheet(
            f"background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 14px; color: {TEXT_MUTED};"
        )
        return preview

    def _page_camera(self):

        page, layout = self._page()

        layout.addWidget(_label("Let's check your camera", PRIMARY_TEXT, 24, 700))
        layout.addWidget(_label(
            f"Hold a hand up in front of the camera. {APP_NAME} only looks; "
            "nothing is recorded or uploaded.",
            SECONDARY_TEXT, 14,
        ))

        self.camera_preview = self._preview()
        layout.addWidget(self.camera_preview, 0, Qt.AlignHCenter)

        self.camera_status = _label("", SECONDARY_TEXT, 14, 600, center=True)
        self.camera_status.setAccessibleName("Camera check")
        layout.addWidget(self.camera_status)
        layout.addStretch()
        return page

    def _page_try(self):

        page, layout = self._page()

        layout.addWidget(_label("Try your first gesture", PRIMARY_TEXT, 24, 700))
        layout.addWidget(_label("Give the camera a thumbs up 👍", SECONDARY_TEXT, 15))

        self.try_preview = self._preview()
        layout.addWidget(self.try_preview, 0, Qt.AlignHCenter)

        self.try_status = _label("", SECONDARY_TEXT, 14, 600, center=True)
        self.try_status.setAccessibleName("Gesture check")
        layout.addWidget(self.try_status)

        tips = _label(
            "• Record your own gestures and moves in <b>Gesture Studio</b><br>"
            "• Swipe left or right in <b>Presentation Studio</b> to change slides<br>"
            "• On Home, point your finger to write on the fog",
            SECONDARY_TEXT, 13,
        )
        tips.setTextFormat(Qt.RichText)
        layout.addWidget(tips)
        layout.addStretch()
        return page

    # -----------------------------------------------------
    # NAVIGATION
    # -----------------------------------------------------

    def _button(self, text, primary=False, quiet=False):
        button = QPushButton(text)
        button.setCursor(Qt.PointingHandCursor)
        if primary:
            style = f"""
                QPushButton {{ background: {PRIMARY}; color: {ON_PRIMARY}; border: none;
                    border-radius: 10px; padding: 10px 20px; font-size: 14px; font-weight: 600; }}
                QPushButton:hover {{ background: {PRIMARY_HOVER}; }}
            """
        elif quiet:
            style = f"""
                QPushButton {{ background: transparent; color: {TEXT_MUTED}; border: none;
                    border-radius: 10px; padding: 10px 12px; font-size: 13px; }}
                QPushButton:hover {{ color: {PRIMARY_TEXT}; background: {OVERLAY_1}; }}
            """
        else:
            style = f"""
                QPushButton {{ background: {OVERLAY_1}; color: {PRIMARY_TEXT};
                    border: 1px solid {BORDER}; border-radius: 10px; padding: 10px 16px; font-size: 14px; }}
                QPushButton:hover {{ background: {OVERLAY_2}; }}
            """
        button.setStyleSheet(style)
        return button

    def go(self, index):

        index = max(0, min(index, self.STEPS - 1))
        self.pages.setCurrentIndex(index)

        self.back_button.setVisible(index > 0)
        last = index == self.STEPS - 1
        self.next_button.setText(f"Start using {APP_NAME}" if last else "Continue")
        self.skip_button.setVisible(not last)

        self.dots.setText("  ".join(
            f'<span style="color:{PRIMARY if i == index else BORDER}; font-size:18px;">●</span>'
            for i in range(self.STEPS)
        ))

        # The camera runs only on the camera and gesture steps.
        if index in (2, 3):
            self._start_camera()
        else:
            self._stop_camera()

        if index == 2:
            self._set_camera_status(self.saw_hand)
        if index == 3:
            self._set_try_status(self.did_gesture)

    def _next(self):

        index = self.pages.currentIndex()

        if index == 0:
            set_display_name(self.name_input.text())

        if index == self.STEPS - 1:
            self.finish()
            return

        self.go(index + 1)

    def _pick_theme(self, name):
        self.chosen_theme = name
        SettingsManager().set_setting(theme_module.SETTING_KEY, name)
        if name != theme_module.THEME_NAME:
            self.theme_note.setText(f"{APP_NAME} will restart once at the end to apply it.")
        else:
            self.theme_note.setText("")

    def finish(self):
        if self.pages.currentIndex() == 0:
            set_display_name(self.name_input.text())
        mark_welcomed()
        self.accept()

    @property
    def theme_changed(self):
        return self.chosen_theme != theme_module.THEME_NAME

    # -----------------------------------------------------
    # CAMERA
    # -----------------------------------------------------

    def _start_camera(self):

        if self.worker is not None:
            return

        self.thread = QThread(self)
        self.worker = CameraPreviewWorker()
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.frame_ready.connect(self._on_frame)
        self.worker.error.connect(self._on_camera_error)
        self.worker.finished.connect(self.thread.quit)

        self.thread.start()

    def _stop_camera(self):

        worker, thread = self.worker, self.thread
        self.worker = None
        self.thread = None

        if worker is not None:
            worker.stop()

        if thread is not None:
            thread.quit()
            thread.wait(5000)

    @Slot(QImage, object, object, float)
    def _on_frame(self, image, vector, builtin, confidence):

        if self.worker is None:
            return

        pixmap = QPixmap.fromImage(image).scaled(
            PREVIEW_W, PREVIEW_H, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

        index = self.pages.currentIndex()

        if index == 2:
            self.camera_preview.setPixmap(pixmap)
            if vector is not None and not self.saw_hand:
                self.saw_hand = True
            self._set_camera_status(self.saw_hand, hand_now=vector is not None)

        elif index == 3:
            self.try_preview.setPixmap(pixmap)
            if builtin == THUMBS_UP and not self.did_gesture:
                self.did_gesture = True
            self._set_try_status(self.did_gesture)

    def _set_camera_status(self, ok, hand_now=False):
        if ok:
            self.camera_status.setText(f"✓  {APP_NAME} can see your hand")
            self.camera_status.setStyleSheet(f"color: {SUCCESS}; font-size: 14px; font-weight: 600; background: transparent;")
        else:
            self.camera_status.setText("Waiting for a hand…")
            self.camera_status.setStyleSheet(f"color: {SECONDARY_TEXT}; font-size: 14px; font-weight: 600; background: transparent;")

    def _set_try_status(self, ok):
        if ok:
            self.try_status.setText("✓  Nice! That's how gestures work.")
            self.try_status.setStyleSheet(f"color: {SUCCESS}; font-size: 14px; font-weight: 600; background: transparent;")
        else:
            self.try_status.setText("Waiting for a thumbs up…")
            self.try_status.setStyleSheet(f"color: {SECONDARY_TEXT}; font-size: 14px; font-weight: 600; background: transparent;")

    @Slot(str)
    def _on_camera_error(self, message):
        self.worker = None
        text = (
            "Couldn't open the camera. Close apps that might be using it "
            "(Zoom, Teams, the Camera app), and check Windows Settings → "
            "Privacy & security → Camera → \"Let desktop apps access your "
            "camera\". You can skip this step and try later."
        )
        for preview in (self.camera_preview, self.try_preview):
            preview.setText("Camera unavailable")
        for status in (self.camera_status, self.try_status):
            status.setText(text)
            status.setStyleSheet(f"color: {WARNING}; font-size: 13px; background: transparent;")

    def reject(self):
        # Closing the window counts as skipping: don't show it every launch.
        mark_welcomed()
        super().reject()

    def done(self, result):
        self._stop_camera()
        super().done(result)

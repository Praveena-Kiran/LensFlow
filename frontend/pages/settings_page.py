"""
Settings page: accessibility options for gesture recognition, and where
Wield keeps its data. Changes save immediately and apply the next time a
studio starts listening.
"""

import os
import platform
import subprocess

from PySide6.QtCore import QObject, QThread, Qt, Signal, Slot
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from frontend.pages.studio_page import StudioPage
from frontend.styles.theme import (
    OVERLAY_1,
    BORDER,
    ON_PRIMARY,
    PRIMARY,
    PRIMARY_HOVER,
    PRIMARY_TEXT,
    SECONDARY_TEXT,
    SURFACE,
    SURFACE_HOVER,
    TEXT_MUTED,
)
from frontend.styles import theme as theme_module
from backend.paths import user_data_dir
from backend.settings.settings_manager import SettingsManager
from backend.settings import gesture_settings
from backend.settings.gesture_settings import ARM_TIMEOUT_CHOICES, HOLD_TIME_CHOICES
from backend.app_info import APP_NAME
from backend.voice import model as voice_model



class _ModelDownloader(QObject):
    """Downloads the speech model off the UI thread."""

    progress = Signal(int, int)
    done = Signal(str)        # "" on success, else the error message

    @Slot()
    def run(self):
        try:
            voice_model.download_model(
                progress=lambda done, total: self.progress.emit(done, total)
            )
        except Exception as e:
            self.done.emit(str(e) or "The download failed.")
            return
        self.done.emit("")


class SettingsPage(StudioPage):

    # The main window restarts the app (themes apply at startup).
    restart_requested = Signal()

    # The display name changed (greeting and sidebar update).
    name_changed = Signal()

    # "Show welcome again" (About section).
    welcome_requested = Signal()

    def __init__(self, parent=None):

        super().__init__(
            title="Settings",
            subtitle=f"Make {APP_NAME} work the way you move.",
            parent=parent,
        )

        self.settings = gesture_settings.load()

        self.setStyleSheet(self.styleSheet() + f"""
            QComboBox {{
                background: {SURFACE}; color: {PRIMARY_TEXT};
                border: 1px solid {BORDER}; border-radius: 8px;
                padding: 6px 10px; min-height: 24px; min-width: 160px;
            }}
            QWidget#SettingsRow {{ background: transparent; }}
            QCheckBox {{ color: {PRIMARY_TEXT}; font-size: 14px; spacing: 10px; background: transparent; }}
            QCheckBox::indicator {{
                width: 18px; height: 18px; border-radius: 5px;
                border: 1px solid {BORDER}; background: {SURFACE};
            }}
            QCheckBox::indicator:checked {{ background: {PRIMARY}; border: 1px solid {PRIMARY}; }}
            QSlider {{ background: transparent; }}
            QSlider::groove:horizontal {{
                height: 6px; border-radius: 3px; background: {SURFACE_HOVER};
            }}
            QSlider::sub-page:horizontal {{
                height: 6px; border-radius: 3px; background: {PRIMARY};
            }}
            QSlider::handle:horizontal {{
                width: 18px; height: 18px; margin: -6px 0;
                border-radius: 9px; background: white;
            }}
        """)

        self._build_you()

        self._build_appearance()

        self._section("Recognition")

        # Sensitivity -------------------------------------------------

        self.sensitivity = QSlider(Qt.Horizontal)
        self.sensitivity.setRange(0, 100)
        self.sensitivity.setSingleStep(5)
        self.sensitivity.setPageStep(10)
        self.sensitivity.setValue(self.settings["sensitivity"])
        self.sensitivity.setAccessibleName("Matching sensitivity")
        self.sensitivity.valueChanged.connect(self._on_sensitivity)

        slider_row = QHBoxLayout()
        slider_row.addWidget(self._muted("Strict"))
        slider_row.addWidget(self.sensitivity, 1)
        slider_row.addWidget(self._muted("Forgiving"))

        self._row(
            "Sensitivity",
            "More forgiving accepts poses and movements that are less exact, "
            "helpful with tremor or limited movement. Stricter avoids "
            "accidental triggers.",
            slider_row,
        )

        # Hold time ---------------------------------------------------

        self.hold_time = QComboBox()
        self.hold_time.setAccessibleName("Hold time")
        for seconds in HOLD_TIME_CHOICES:
            self.hold_time.addItem(
                "Instant" if seconds == 0 else f"{seconds:g} seconds",
                seconds,
            )
        self._select(self.hold_time, self.settings["hold_time"])
        self.hold_time.currentIndexChanged.connect(
            lambda: self._save("hold_time", self.hold_time.currentData())
        )

        self._row(
            "Hold to trigger",
            "How long a pose must be held before it does anything. "
            "Motions are not affected.",
            self.hold_time,
        )

        self._section("Activation gesture")

        # Activation --------------------------------------------------

        self.require_arm = QCheckBox("Only respond after an activation gesture")
        self.require_arm.setChecked(self.settings["require_arm"])
        self.require_arm.toggled.connect(self._on_require_arm)

        self._row(
            None,
            "Stops everyday hand movements, like talking with your hands on "
            "a call, from triggering anything.",
            self.require_arm,
        )

        self.arm_gesture = QComboBox()
        self.arm_gesture.setAccessibleName("Activation gesture")
        self._fill_gestures()
        self.arm_gesture.currentIndexChanged.connect(
            lambda: self._save("arm_gesture", self.arm_gesture.currentData())
        )

        self._row("Gesture", "Make this to start responding.", self.arm_gesture)

        self.arm_timeout = QComboBox()
        self.arm_timeout.setAccessibleName("Switch off after")
        for seconds in ARM_TIMEOUT_CHOICES:
            self.arm_timeout.addItem(f"{seconds} seconds without gestures", seconds)
        self._select(self.arm_timeout, self.settings["arm_timeout"])
        self.arm_timeout.currentIndexChanged.connect(
            lambda: self._save("arm_timeout", self.arm_timeout.currentData())
        )

        self._row("Switch off after", None, self.arm_timeout)

        self._on_require_arm(self.settings["require_arm"], save=False)

        self._section("Feedback")

        self.sound_feedback = QCheckBox("Play soft sounds")
        self.sound_feedback.setChecked(self.settings["sound_feedback"])
        self.sound_feedback.toggled.connect(
            lambda checked: self._save("sound_feedback", bool(checked))
        )
        self._row(
            None,
            "A short chime when Wield starts listening and when it runs an "
            "action, so you know it worked without looking.",
            self.sound_feedback,
        )

        self.feedback_overlay = QCheckBox("Show what Wield did on top of other windows")
        self.feedback_overlay.setChecked(self.settings["feedback_overlay"])
        self.feedback_overlay.toggled.connect(
            lambda checked: self._save("feedback_overlay", bool(checked))
        )
        self._row(
            None,
            "A small note at the bottom of the screen, e.g. \u201c\U0001F44D \u2192 "
            "Next slide\u201d. It shows over full-screen slideshows and never "
            "gets in the way of clicks.",
            self.feedback_overlay,
        )

        self._build_voice()

        self._section("Your data")

        data_button = QPushButton("Open data folder")
        data_button.setCursor(Qt.PointingHandCursor)
        data_button.setStyleSheet(f"""
            QPushButton {{
                background: {OVERLAY_1}; color: {PRIMARY_TEXT};
                border: 1px solid {BORDER}; border-radius: 10px;
                padding: 9px 16px; font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ border: 1px solid {PRIMARY}; }}
        """)
        data_button.clicked.connect(self._open_data_folder)

        self._row(
            "Stored on this computer",
            f"Studios, settings and your recorded gestures: {user_data_dir()}",
            data_button,
        )

        self._build_about()

        self.content_layout.addStretch()

    # -----------------------------------------------------
    # ABOUT
    # -----------------------------------------------------

    def _small_button(self, text, handler):
        button = QPushButton(text)
        button.setCursor(Qt.PointingHandCursor)
        button.setStyleSheet(f"""
            QPushButton {{
                background: {OVERLAY_1}; color: {PRIMARY_TEXT};
                border: 1px solid {BORDER}; border-radius: 10px;
                padding: 9px 16px; font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ border: 1px solid {PRIMARY}; }}
        """)
        button.clicked.connect(handler)
        return button

    def _build_about(self):

        from backend.app_info import APP_NAME, VERSION

        self._section("About")

        self._row(
            f"{APP_NAME} {VERSION}",
            "Your camera is processed on this computer and never recorded or "
            "uploaded. Gestures, notes and activity are stored only in your "
            "data folder above.",
            QWidget(),
        )

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addWidget(self._small_button("Open log", self._open_log))
        buttons.addWidget(self._small_button("Report a problem", self._report_problem))
        buttons.addWidget(self._small_button("Show welcome again", self.welcome_requested.emit))
        buttons.addStretch()

        self._row(
            None,
            "If something isn't working, the log helps explain why. Reporting "
            "opens a GitHub issue; attach the log if you can.",
            buttons,
        )

    def _open_log(self):
        from backend.app_log import log_path
        path = log_path()
        if not os.path.exists(path):
            open(path, "a").close()
        self._open_path(path)

    def _report_problem(self):
        from urllib.parse import urlencode
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        from backend.app_info import APP_NAME, ISSUES_URL, VERSION

        body = (
            "**What happened?**\n\n\n"
            "**What did you expect?**\n\n\n"
            f"---\n{APP_NAME} {VERSION} on {platform.system()} {platform.release()}\n"
            "(Settings → About → Open log, and attach wield.log if you can.)"
        )
        QDesktopServices.openUrl(QUrl(ISSUES_URL + "?" + urlencode({"body": body})))

    # -----------------------------------------------------
    # YOU
    # -----------------------------------------------------

    def _build_you(self):

        from backend.settings.user import display_name

        self._section("You")

        self.name_input = QLineEdit(display_name())
        self.name_input.setPlaceholderText("Your name")
        self.name_input.setAccessibleName("Your name")
        self.name_input.setMaxLength(40)
        self.name_input.setFixedWidth(280)
        self.name_input.setStyleSheet(f"""
            QLineEdit {{
                background: {SURFACE}; color: {PRIMARY_TEXT};
                border: 1px solid {BORDER}; border-radius: 8px;
                padding: 8px 10px; font-size: 14px;
            }}
            QLineEdit:focus {{ border: 1px solid {PRIMARY}; }}
        """)
        self.name_input.editingFinished.connect(self._on_name)

        self._row("Your name", "Used in the greeting on Home.", self.name_input)

    def _on_name(self):
        from backend.settings.user import set_display_name
        set_display_name(self.name_input.text())
        self.status_label.setText("Status: Saved.")
        self.name_changed.emit()

    # -----------------------------------------------------
    # APPEARANCE
    # -----------------------------------------------------

    def _build_appearance(self):

        self._section("Appearance")

        row = QHBoxLayout()
        row.setSpacing(12)

        self.theme_group = QButtonGroup(self)
        self.theme_group.setExclusive(True)

        saved = SettingsManager().get_setting(theme_module.SETTING_KEY) or theme_module.DEFAULT_THEME

        for name, palette in theme_module.THEMES.items():

            button = QPushButton(palette["label"])
            button.setCheckable(True)
            button.setChecked(name == saved)
            button.setCursor(Qt.PointingHandCursor)
            button.setAccessibleName(f"{palette['label']} theme")
            button.setFixedSize(132, 84)
            # Each swatch is drawn in its own theme's colours.
            button.setStyleSheet(f"""
                QPushButton {{
                    background: {palette['BG_DARK']};
                    color: {palette['PRIMARY_TEXT']};
                    border: 2px solid {palette['BORDER']};
                    border-radius: 14px;
                    font-size: 13px; font-weight: 600;
                    padding-top: 34px;
                }}
                QPushButton:hover {{ border: 2px solid {palette['PRIMARY_HOVER']}; }}
                QPushButton:checked {{ border: 2px solid {palette['PRIMARY']}; }}
            """)

            dot = QLabel(button)
            dot.setGeometry(14, 14, 22, 22)
            dot.setStyleSheet(
                f"background: {palette['PRIMARY']}; border-radius: 11px; border: none;"
            )
            surface = QLabel(button)
            surface.setGeometry(42, 14, 76, 22)
            surface.setStyleSheet(
                f"background: {palette['SURFACE']}; border-radius: 7px; "
                f"border: 1px solid {palette['BORDER']};"
            )

            button.clicked.connect(lambda checked=False, n=name: self._on_theme(n))
            self.theme_group.addButton(button)
            row.addWidget(button)

        row.addStretch()

        box = self._row(
            "Theme",
            "Galaxy and Jungle add a little scenery behind the app.",
            row,
        )

        self.restart_row = QHBoxLayout()

        self.restart_note = QLabel(f"Restart {APP_NAME} to apply the new theme.")
        self.restart_note.setStyleSheet(
            f"color: {SECONDARY_TEXT}; font-size: 13px; background: transparent;"
        )

        self.restart_button = QPushButton("Restart now")
        self.restart_button.setCursor(Qt.PointingHandCursor)
        self.restart_button.setStyleSheet(f"""
            QPushButton {{
                background: {PRIMARY}; color: {ON_PRIMARY}; border: none;
                border-radius: 10px; padding: 9px 16px;
                font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {PRIMARY_HOVER}; }}
        """)
        self.restart_button.clicked.connect(self.restart_requested.emit)

        self.restart_row.addWidget(self.restart_note)
        self.restart_row.addWidget(self.restart_button)
        self.restart_row.addStretch()
        box.layout().addLayout(self.restart_row)

        self._show_restart(saved != theme_module.THEME_NAME)

    def _show_restart(self, visible):
        self.restart_note.setVisible(visible)
        self.restart_button.setVisible(visible)

    def _on_theme(self, name):
        SettingsManager().set_setting(theme_module.SETTING_KEY, name)
        self._show_restart(name != theme_module.THEME_NAME)
        self.status_label.setText(f"Status: {theme_module.THEMES[name]['label']} theme saved.")

    # -----------------------------------------------------
    # LAYOUT HELPERS
    # -----------------------------------------------------

    # -----------------------------------------------------
    # VOICE COMMANDS
    # -----------------------------------------------------

    def _build_voice(self):

        self._section("Voice commands")

        self.voice_enabled = QCheckBox("Listen for spoken commands")
        self.voice_enabled.setChecked(self.settings["voice_enabled"])
        self.voice_enabled.toggled.connect(self._on_voice_enabled)
        self._row(
            None,
            "Say a phrase instead of (or as well as) making a gesture, e.g. "
            "\u201cHey Wield, next slide\u201d. Choose phrases for each action in "
            "Gesture Studio. Speech is recognised on this computer: no audio "
            "is recorded or sent anywhere.",
            self.voice_enabled,
        )

        self.voice_wake_word = QCheckBox("Only respond after \u201cHey Wield\u201d")
        self.voice_wake_word.setChecked(self.settings["voice_wake_word"])
        self.voice_wake_word.toggled.connect(
            lambda checked: self._save("voice_wake_word", bool(checked))
        )
        self._row(
            None,
            "Recommended, so words in your talk (\u201c\u2026as the next slide "
            "shows\u2026\u201d) don't change anything. You can say it on its own "
            "and then the command within 5 seconds.",
            self.voice_wake_word,
        )

        self.voice_model_status = QLabel()
        self.voice_model_status.setWordWrap(True)
        self.voice_model_status.setStyleSheet(
            f"color: {SECONDARY_TEXT}; font-size: 13px; border: none; background: transparent;"
        )

        self.voice_download = self._small_button(
            f"Download speech model ({voice_model.MODEL_SIZE_MB} MB)",
            self._download_voice_model,
        )

        model_row = QHBoxLayout()
        model_row.addWidget(self.voice_download)
        model_row.addWidget(self.voice_model_status, 1)
        self._row("Speech model", None, model_row)

        self._download_thread = None
        self._refresh_voice_status()

    def _on_voice_enabled(self, checked):
        self._save("voice_enabled", bool(checked))
        self._refresh_voice_status()

    def _refresh_voice_status(self, message=None):
        ready = voice_model.model_ready()
        available = voice_model.vosk_available()
        downloading = self._download_thread is not None

        self.voice_download.setVisible(available and not ready)
        self.voice_download.setEnabled(not downloading)

        if message:
            text = message
        elif not available:
            text = ("Voice commands need two extra packages: "
                    "pip install vosk sounddevice")
        elif ready:
            text = "\u2713 Installed. Voice commands work offline."
        else:
            text = "Needed once for voice commands. Stored on this computer."
        self.voice_model_status.setText(text)

    def _download_voice_model(self):
        if self._download_thread is not None:
            return

        self._download_thread = QThread(self)
        self._downloader = _ModelDownloader()
        self._downloader.moveToThread(self._download_thread)
        self._download_thread.started.connect(self._downloader.run)
        self._downloader.progress.connect(self._on_download_progress)
        self._downloader.done.connect(self._on_download_done)
        self._download_thread.start()
        self._refresh_voice_status("Downloading\u2026")

    @Slot(int, int)
    def _on_download_progress(self, done, total):
        if total:
            self.voice_model_status.setText(
                f"Downloading\u2026 {done * 100 // total}% "
                f"({done // 1_000_000} of {total // 1_000_000} MB)"
            )

    @Slot(str)
    def _on_download_done(self, error):
        thread = self._download_thread
        self._download_thread = None
        if thread is not None:
            thread.quit()
            thread.wait(5000)
        self._refresh_voice_status(
            f"\u26a0 Download failed: {error}" if error else None
        )

    def _section(self, title):
        label = QLabel(title)
        label.setStyleSheet(f"""
            color: {PRIMARY_TEXT}; font-size: 17px; font-weight: 700;
            margin-top: 8px; border: none; background: transparent;
        """)
        self.content_layout.addWidget(label)

    def _muted(self, text):
        label = QLabel(text)
        label.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 12px; border: none; background: transparent;"
        )
        return label

    def _row(self, title, description, control):

        box = QWidget()
        box.setObjectName("SettingsRow")
        box.setAttribute(Qt.WA_StyledBackground, True)
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 4)
        layout.setSpacing(6)

        if title:
            heading = QLabel(title)
            heading.setStyleSheet(
                f"color: {PRIMARY_TEXT}; font-size: 14px; font-weight: 600; "
                "border: none; background: transparent;"
            )
            layout.addWidget(heading)

        if description:
            text = QLabel(description)
            text.setWordWrap(True)
            text.setStyleSheet(
                f"color: {SECONDARY_TEXT}; font-size: 13px; border: none; "
                "background: transparent;"
            )
            layout.addWidget(text)

        if isinstance(control, QHBoxLayout):
            layout.addLayout(control)
        else:
            layout.addWidget(control, 0, Qt.AlignLeft)

        self.content_layout.addWidget(box)

        return box

    @staticmethod
    def _select(combo, value):
        for i in range(combo.count()):
            if combo.itemData(i) == value:
                combo.setCurrentIndex(i)
                return

    def _fill_gestures(self):

        from backend.gestures.custom_gestures import CustomGestureStore
        from backend.gestures.google_gesture_recognizer import BUILTIN_GESTURE_NAMES
        from backend.gestures.motions import BUILTIN_MOTION_NAMES, MotionStore

        names = (
            list(BUILTIN_GESTURE_NAMES)
            + CustomGestureStore().names()
            + list(BUILTIN_MOTION_NAMES)
            + MotionStore().names()
        )

        self.arm_gesture.blockSignals(True)
        self.arm_gesture.clear()

        for name in names:
            self.arm_gesture.addItem(name, name)

        current = self.settings["arm_gesture"]
        if self.arm_gesture.findData(current) < 0:
            self.arm_gesture.addItem(f"{current} (not found)", current)

        self._select(self.arm_gesture, current)
        self.arm_gesture.blockSignals(False)

    # -----------------------------------------------------
    # CHANGES
    # -----------------------------------------------------

    def _save(self, key, value):
        gesture_settings.save(key, value)
        self.settings[key] = value
        self.status_label.setText("Status: Saved. Applies next time a studio starts listening.")

    def _on_sensitivity(self, value):
        self._save("sensitivity", int(value))

    def _on_require_arm(self, checked, save=True):
        if save:
            self._save("require_arm", bool(checked))
        self.arm_gesture.setEnabled(checked)
        self.arm_timeout.setEnabled(checked)

    def _open_data_folder(self):
        self._open_path(user_data_dir())

    def _open_path(self, path):
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    def showEvent(self, event):
        # Pick up gestures recorded since the page was built.
        self._fill_gestures()
        super().showEvent(event)

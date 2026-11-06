"""
Settings page: accessibility options for gesture recognition, and where
LensFlow keeps its data. Changes save immediately and apply the next time a
studio starts listening.
"""

import os
import platform
import subprocess

from PySide6.QtCore import Qt, Signal
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


class SettingsPage(StudioPage):

    # The main window restarts the app (themes apply at startup).
    restart_requested = Signal()

    # The display name changed (greeting and sidebar update).
    name_changed = Signal()

    def __init__(self, parent=None):

        super().__init__(
            title="Settings",
            subtitle="Make LensFlow work the way you move.",
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

        self.content_layout.addStretch()

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

        self.restart_note = QLabel("Restart LensFlow to apply the new theme.")
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
        path = user_data_dir()
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

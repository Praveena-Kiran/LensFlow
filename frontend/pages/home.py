"""
Home: greeting, "Your window" (the foggy camera you can write on), a Today
card with real information (next routine, recent activity), and the list of
studios.

Public API used by main.py (unchanged from the previous Home):
    signals: studio_selected(str), create_studio_requested(),
             launch_all_events_requested(str),
             launch_specific_event_requested(str, dict),
             history_requested()
    methods: load_studios(), refresh_studios(), get_config_path()
"""

import json
from datetime import datetime, timedelta

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from frontend.components.fog_window import FogWindow
from frontend.styles.theme import (
    BORDER,
    ON_PRIMARY,
    OVERLAY_1,
    OVERLAY_2,
    OVERLAY_BORDER,
    PAGE_BG,
    PRIMARY,
    PRIMARY_HOVER,
    PRIMARY_MUTED,
    PRIMARY_TEXT,
    SECONDARY_TEXT,
    SUCCESS,
    SURFACE,
    TEXT_MUTED,
)
from backend.paths import user_config_path
from backend.routines import ActivityLog, RoutineStore, parse_time
from backend.settings.user import display_name


# Built-in studios and what they actually do. Shown instead of the saved
# description, which older versions wrote with features LensFlow doesn't have.
BUILT_IN_DESCRIPTIONS = {
    "Presentation Studio": "Control PowerPoint slides with gestures and swipes.",
    "Coding Studio": "Open your development workspace in one go.",
    "Gesture Studio": "Record, test and assign your gestures and motions.",
    "Automation Studio": "Build your own gesture-triggered automations.",
}

BUILT_IN_STUDIOS = set(BUILT_IN_DESCRIPTIONS)


def greeting(now=None):
    hour = (now or datetime.now()).hour
    if hour < 12:
        return "Good morning"
    if hour < 18:
        return "Good afternoon"
    return "Good evening"


def humanize_day(when, now=None):
    if when is None:
        return "Never"
    now = now or datetime.now()
    days = (now.date() - when.date()).days
    if days <= 0:
        return "Today"
    if days == 1:
        return "Yesterday"
    if days < 7:
        return f"{days} days ago"
    return when.strftime("%d %b")


def next_run(routine, now=None):
    """The next datetime a routine will run, or None."""
    now = now or datetime.now()
    if not routine.get("enabled", True):
        return None
    minutes = parse_time(routine["time"])
    for offset in range(0, 8):
        day = (now + timedelta(days=offset)).date()
        if day.weekday() not in routine.get("days", []):
            continue
        if offset == 0 and routine.get("last_run") == day.isoformat():
            continue
        at = datetime(day.year, day.month, day.day, minutes // 60, minutes % 60)
        if at >= now - timedelta(minutes=30):
            return at
    return None


def _label(text, color=PRIMARY_TEXT, size=14, weight=400, extra=""):
    label = QLabel(text)
    label.setStyleSheet(
        f"color: {color}; font-size: {size}px; font-weight: {weight}; "
        f"background: transparent; border: none; {extra}"
    )
    return label


def _eyebrow(text, color=TEXT_MUTED):
    return _label(text.upper(), color, 11, 600, "letter-spacing: 1px;")


def _button(text, primary=False, quiet=False, accent_text=False):
    button = QPushButton(text)
    button.setCursor(Qt.PointingHandCursor)
    if primary:
        style = f"""
            QPushButton {{ background: {PRIMARY}; color: {ON_PRIMARY}; border: none;
                border-radius: 12px; padding: 0 18px; min-height: 40px;
                font-size: 13px; font-weight: 600; }}
            QPushButton:hover {{ background: {PRIMARY_HOVER}; }}
        """
    elif quiet:
        color = PRIMARY if accent_text else SECONDARY_TEXT
        style = f"""
            QPushButton {{ background: transparent; color: {color}; border: none;
                border-radius: 10px; padding: 0 10px; min-height: 36px; font-size: 13px; }}
            QPushButton:hover {{ color: {PRIMARY_TEXT}; background: {OVERLAY_1}; }}
        """
    else:
        style = f"""
            QPushButton {{ background: transparent; color: {PRIMARY_TEXT};
                border: 1px solid {OVERLAY_BORDER}; border-radius: 10px;
                padding: 0 14px; min-height: 36px; font-size: 13px; }}
            QPushButton:hover {{ background: {OVERLAY_1}; border: 1px solid {PRIMARY}; }}
        """
    button.setStyleSheet(style)
    return button


class HomePage(QWidget):

    studio_selected = Signal(str)
    create_studio_requested = Signal()
    launch_all_events_requested = Signal(str)
    launch_specific_event_requested = Signal(str, dict)
    history_requested = Signal()

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setObjectName("HomePage")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            QWidget#HomePage {{ background-color: {PAGE_BG}; }}
            QFrame#Card {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 24px; }}
            QFrame#StudioRow {{ background: transparent; border: none; border-top: 1px solid {BORDER}; }}
            QFrame#StudioRow:hover {{ background: {OVERLAY_1}; }}
        """)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        scroll.viewport().setAutoFillBackground(False)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        scroll.setWidget(content)

        centre = QHBoxLayout(content)
        centre.setContentsMargins(48, 36, 48, 40)

        column = QWidget()
        column.setMaximumWidth(1180)
        column.setStyleSheet("background: transparent;")
        centre.addWidget(column)

        self.main = QVBoxLayout(column)
        self.main.setContentsMargins(0, 0, 0, 0)
        self.main.setSpacing(32)

        self._build_header()
        self._build_live_row()
        self._build_studios()

        self.main.addStretch()

        self.refresh_studios()

    # -----------------------------------------------------
    # HEADER
    # -----------------------------------------------------

    def _build_header(self):

        row = QHBoxLayout()

        text = QVBoxLayout()
        text.setSpacing(6)

        self.date_label = _label("", TEXT_MUTED, 13)
        self.greeting_label = _label("", PRIMARY_TEXT, 32, 600, "letter-spacing: -0.5px;")

        text.addWidget(self.date_label)
        text.addWidget(self.greeting_label)

        row.addLayout(text)
        row.addStretch()

        self.camera_pill = _label("", SECONDARY_TEXT, 13, 400,
                                  f"background: {OVERLAY_1}; border-radius: 16px; padding: 8px 14px;")
        row.addWidget(self.camera_pill, 0, Qt.AlignBottom)

        self.main.addLayout(row)

    def _update_header(self):
        now = datetime.now()
        self.date_label.setText(f"{now.strftime('%A')}, {now.day} {now.strftime('%B')}")
        name = display_name()
        self.greeting_label.setText(f"{greeting(now)}, {name}" if name else greeting(now))

    def _set_camera_pill(self, on):
        dot = SUCCESS if on else TEXT_MUTED
        self.camera_pill.setText(
            f'<span style="color:{dot};">●</span>&nbsp; Camera {"on" if on else "off"}'
        )

    # -----------------------------------------------------
    # YOUR WINDOW + TODAY
    # -----------------------------------------------------

    def _build_live_row(self):

        row = QHBoxLayout()
        row.setSpacing(20)

        # Your window ------------------------------------------------
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 20)
        layout.setSpacing(14)

        top = QHBoxLayout()
        top.addWidget(_eyebrow("Your window"))
        top.addStretch()

        filters = QFrame()
        filters.setStyleSheet(f"QFrame {{ background: {OVERLAY_1}; border-radius: 10px; border: none; }}")
        filters_layout = QHBoxLayout(filters)
        filters_layout.setContentsMargins(3, 3, 3, 3)
        filters_layout.setSpacing(2)

        self.filter_group = QButtonGroup(self)
        for name in ("Fog", "Clear", "Mono"):
            b = QPushButton(name)
            b.setCheckable(True)
            b.setChecked(name == "Fog")
            b.setCursor(Qt.PointingHandCursor)
            b.setAccessibleName(f"{name} filter")
            b.setStyleSheet(f"""
                QPushButton {{ background: transparent; color: {SECONDARY_TEXT}; border: none;
                    border-radius: 8px; padding: 0 12px; min-height: 28px; font-size: 12px; }}
                QPushButton:checked {{ background: {OVERLAY_2}; color: {PRIMARY_TEXT}; font-weight: 600; }}
            """)
            b.clicked.connect(lambda checked=False, n=name.lower(): self.fog.set_filter(n))
            self.filter_group.addButton(b)
            filters_layout.addWidget(b)

        top.addWidget(filters)
        layout.addLayout(top)

        self.fog = FogWindow()
        self.fog.setMinimumHeight(230)
        layout.addWidget(self.fog, 1)

        controls = QHBoxLayout()
        controls.setSpacing(10)

        self.camera_button = _button("Start camera", primary=True)
        self.camera_button.clicked.connect(self._toggle_camera)

        save = _button("Save note")
        save.clicked.connect(self.fog.save_note)

        wipe = _button("Wipe", quiet=True)
        wipe.clicked.connect(self.fog.wipe)

        self.fog_status = _label("Point to write · fist to pause · open palm to wipe", TEXT_MUTED, 12)
        self.fog_status.setWordWrap(True)

        controls.addWidget(self.camera_button)
        controls.addWidget(save)
        controls.addWidget(wipe)
        controls.addSpacing(6)
        controls.addWidget(self.fog_status, 1)
        layout.addLayout(controls)

        self.fog.status_changed.connect(self.fog_status.setText)
        self.fog.camera_state_changed.connect(self._on_camera_state)

        row.addWidget(card, 3)

        # Today ------------------------------------------------------
        today = QFrame()
        today.setObjectName("Card")
        today.setMinimumWidth(280)
        t = QVBoxLayout(today)
        t.setContentsMargins(24, 22, 24, 22)
        t.setSpacing(10)

        t.addWidget(_eyebrow("Next routine", PRIMARY))
        self.next_routine = _label("", PRIMARY_TEXT, 15, 500)
        self.next_routine.setWordWrap(True)
        t.addWidget(self.next_routine)

        t.addSpacing(10)
        t.addWidget(_eyebrow("Recently"))

        self.recent_layout = QVBoxLayout()
        self.recent_layout.setSpacing(8)
        t.addLayout(self.recent_layout)

        t.addStretch()

        history = _button("See history", quiet=True, accent_text=True)
        history.clicked.connect(self.history_requested.emit)
        t.addWidget(history, 0, Qt.AlignLeft)

        row.addWidget(today, 2)

        self.main.addLayout(row)
        self._set_camera_pill(False)

    def _toggle_camera(self):
        if self.fog.camera_running:
            self.fog.stop_camera()
        else:
            self.fog.start_camera()

    def _on_camera_state(self, on):
        self.camera_button.setText("Stop camera" if on else "Start camera")
        self._set_camera_pill(on)

    def _update_today(self):

        upcoming = []
        for r in RoutineStore().routines:
            at = next_run(r)
            if at is not None:
                upcoming.append((at, r))
        upcoming.sort(key=lambda item: item[0])

        if upcoming:
            at, r = upcoming[0]
            verb = {"studio": "Open", "launch": "Launch"}.get(r["kind"], "Run")
            when = "today" if at.date() == datetime.now().date() else at.strftime("%A")
            self.next_routine.setText(f"{verb} {r['target']} at {r['time']}, {when}")
        else:
            self.next_routine.setText("None yet. LensFlow will suggest one when it spots a habit.")

        while self.recent_layout.count():
            w = self.recent_layout.takeAt(0).widget()
            if w:
                w.deleteLater()

        entries = sorted(ActivityLog().entries(), key=lambda e: e["_at"], reverse=True)[:3]

        if not entries:
            self.recent_layout.addWidget(_label("Nothing yet.", TEXT_MUTED, 13))

        verbs = {"studio": "Opened", "launch": "Launched", "event": "Ran"}
        for e in entries:
            day = humanize_day(e["_at"])
            when = f"{day.lower() if day in ('Today', 'Yesterday') else day}, {e['_at'].strftime('%H:%M')}"
            label = _label(
                f"{verbs.get(e['kind'], 'Did')} {e['target']} "
                f"<span style='color:{TEXT_MUTED}'>· {when}</span>",
                PRIMARY_TEXT, 13,
            )
            label.setWordWrap(True)
            self.recent_layout.addWidget(label)

    # -----------------------------------------------------
    # STUDIOS
    # -----------------------------------------------------

    def _build_studios(self):

        header = QHBoxLayout()
        header.addWidget(_label("Studios", PRIMARY_TEXT, 18, 600))
        header.addStretch()

        new = _button("+ New studio", quiet=True, accent_text=True)
        new.clicked.connect(self.create_studio_requested.emit)
        header.addWidget(new)

        self.main.addLayout(header)

        self.studios_layout = QVBoxLayout()
        self.studios_layout.setSpacing(0)
        self.main.addLayout(self.studios_layout)

    def get_config_path(self):
        return user_config_path("studios.json")

    def load_studios(self):

        try:
            with open(self.get_config_path(), "r", encoding="utf-8") as f:
                studios = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"❌ Failed to load studios.json: {e}")
            return []

        if not isinstance(studios, list):
            return []

        return [s for s in studios if isinstance(s, dict) and s.get("title")]

    def _last_used(self):
        """{studio title: last activity datetime} from the activity log."""
        latest = {}
        for e in ActivityLog().entries():
            for key in {e.get("target"), e.get("studio")}:
                if key and (key not in latest or e["_at"] > latest[key]):
                    latest[key] = e["_at"]
        return latest

    def refresh_studios(self):

        self._update_header()
        self._update_today()

        while self.studios_layout.count():
            w = self.studios_layout.takeAt(0).widget()
            if w:
                w.deleteLater()

        last_used = self._last_used()

        for studio in self.load_studios():
            self.studios_layout.addWidget(self._studio_row(studio, last_used.get(studio["title"])))

    def _studio_row(self, studio, last_used):

        title = studio["title"]
        custom = studio.get("type") == "custom" or title not in BUILT_IN_STUDIOS

        row = QFrame()
        row.setObjectName("StudioRow")
        row.setAttribute(Qt.WA_StyledBackground, True)
        row.setCursor(Qt.PointingHandCursor)
        row.setMinimumHeight(68)
        row.mousePressEvent = lambda event, t=title: self.studio_selected.emit(t)

        layout = QHBoxLayout(row)
        layout.setContentsMargins(6, 10, 6, 10)
        layout.setSpacing(16)

        words = [w for w in title.replace("Studio", "").split() if w] or [title]
        badge = _label(words[0][:2].capitalize(), PRIMARY, 13, 600,
                       f"background: {PRIMARY_MUTED}; border-radius: 12px;")
        badge.setFixedSize(40, 40)
        badge.setAlignment(Qt.AlignCenter)
        layout.addWidget(badge)

        text = QVBoxLayout()
        text.setSpacing(2)
        text.addWidget(_label(title, PRIMARY_TEXT, 15, 500))

        if custom:
            events = studio.get("events", [])
            gestures = sum(1 for e in events if isinstance(e, dict) and e.get("gesture"))
            meta = f"{len(events)} event{'s' if len(events) != 1 else ''}"
            if gestures:
                meta += f" · {gestures} with gestures"
        else:
            meta = BUILT_IN_DESCRIPTIONS.get(title, studio.get("description", ""))

        meta_label = _label(meta, TEXT_MUTED, 13)
        meta_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        text.addWidget(meta_label)
        layout.addLayout(text, 1)

        layout.addWidget(_label(humanize_day(last_used), TEXT_MUTED, 13))

        if custom:
            launch = _button("Launch")
            launch.setAccessibleName(f"Launch all events in {title}")
            launch.clicked.connect(lambda checked=False, t=title: self.launch_all_events_requested.emit(t))
            layout.addWidget(launch)

        open_button = _button("Edit" if custom else "Open")
        open_button.setAccessibleName(f"{'Edit' if custom else 'Open'} {title}")
        open_button.clicked.connect(lambda checked=False, t=title: self.studio_selected.emit(t))
        layout.addWidget(open_button)

        return row

    # -----------------------------------------------------
    # Compatibility with the previous Home API
    # -----------------------------------------------------

    def launch_studio(self, studio_name):
        self.studio_selected.emit(studio_name)

    def launch_all_events(self, studio_name):
        self.launch_all_events_requested.emit(studio_name)

    def launch_specific_event(self, studio_name, event):
        self.launch_specific_event_requested.emit(studio_name, event)

    def edit_studio(self, studio_name):
        self.studio_selected.emit(studio_name)

import time

import cv2

from PySide6.QtCore import QObject, Signal, Slot

from backend.gestures.google_gesture_recognizer import GoogleGestureRecognizer
from backend.gestures.gesture_stabilizer import GestureStabilizer
from backend.gestures.custom_gestures import CustomGestureMatcher
from backend.profile_manager import ProfileManager
from backend.automation.events import events_for_gesture, profile_events


class GestureWorker(QObject):

    gesture_detected = Signal(str, float)

    # An event to run: {"name", "gesture", "action", "value"}
    custom_event_detected = Signal(dict)

    status_changed = Signal(str)
    error = Signal(str)

    # Emitted when run() has fully exited and the camera is released.
    finished = Signal()

    def __init__(
        self,
        profile_name="presentation",
        custom_studio=None
    ):
        super().__init__()

        self.profile_name = profile_name
        self.custom_studio = custom_studio
        self.running = False

        # Set by stop(). Separate from `running` so a stop requested before
        # run() starts (e.g. leaving a studio straight away) still counts.
        self._stop_requested = False

        self.stabilizer = GestureStabilizer()
        self.recognizer = GoogleGestureRecognizer()

        # The user's own recorded gestures (see Gesture Studio).
        self.custom_matcher = CustomGestureMatcher.from_store()

        # -----------------------------------------------------
        # EVENTS
        # -----------------------------------------------------
        # A custom studio brings its own events; built-in studios use a
        # profile, converted to the same event format. Custom studio events
        # are the studio's own list, so edits made while running apply.

        if self.custom_studio is not None:

            self.events = self.custom_studio.get("events", [])

        else:

            profile_manager = ProfileManager()
            profile_manager.load(profile_name)

            self.events = profile_events(
                profile_manager.current_profile
            )

    def _open_camera(self, attempts=4, delay=0.75):
        """
        Open the webcam, retrying briefly: on Windows the previous studio
        may still be releasing it.
        """

        for attempt in range(attempts):

            if self._stop_requested:
                return None

            camera = cv2.VideoCapture(0)

            if camera.isOpened():
                return camera

            camera.release()

            if attempt < attempts - 1:
                time.sleep(delay)

        return None

    @Slot()
    def run(self):

        try:
            self._run()
        finally:
            self.running = False
            self.finished.emit()

    def _run(self):

        if self._stop_requested:
            return

        self.running = True

        camera = self._open_camera()

        if camera is None:

            if not self._stop_requested:
                self.error.emit(
                    "Could not open webcam. Check that no other app "
                    "is using it."
                )

            return

        try:
            self._loop(camera)
        finally:
            camera.release()

        self.status_changed.emit(
            "STOPPED"
        )

    def _loop(self, camera):

        self.status_changed.emit("READY")

        while not self._stop_requested:

            success, frame = camera.read()

            if not success:

                self.error.emit(
                    "Could not read webcam."
                )

                break

            frame = cv2.flip(
                frame,
                1
            )

            gesture, confidence = (
                self.recognizer.detect(frame)
            )

            # A recorded custom gesture takes priority. Recording rejects
            # poses that look like built-in gestures, so the two don't clash.
            if self.custom_matcher.has_gestures():

                custom_gesture, custom_confidence = (
                    self.custom_matcher.match(
                        self.recognizer.last_landmarks,
                        self.recognizer.last_handedness
                    )
                )

                if custom_gesture:
                    gesture = custom_gesture
                    confidence = custom_confidence

            confirmed_gesture = (
                self.stabilizer.update(
                    gesture,
                    confidence
                )
            )

            if not confirmed_gesture:
                continue

            # -------------------------------------------------
            # GESTURE DETECTED
            # -------------------------------------------------

            self.gesture_detected.emit(
                confirmed_gesture,
                confidence
            )

            # Every studio is a list of events; run the ones this
            # gesture triggers (see backend/automation/events.py).
            for event in events_for_gesture(self.events, confirmed_gesture):

                print("🎯 Event matched:", event.get("name"))

                self.custom_event_detected.emit(event)

    @Slot()
    def stop(self):

        self._stop_requested = True
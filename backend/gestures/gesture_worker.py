import time

import cv2

from PySide6.QtCore import QObject, Signal, Slot

from backend.gestures.google_gesture_recognizer import GoogleGestureRecognizer
from backend.gestures.gesture_stabilizer import GestureStabilizer
from backend.gestures.custom_gestures import CustomGestureMatcher
from backend.profile_manager import ProfileManager


class GestureWorker(QObject):

    gesture_detected = Signal(str, float)
    action_detected = Signal(str)

    # NEW:
    # Sends the complete custom event, including
    # action + selected file path.
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
        # NORMAL PROFILE MODE
        # -----------------------------------------------------

        self.profile_manager = None
        self.gesture_map = {}

        if self.custom_studio is None:

            self.profile_manager = ProfileManager()
            self.profile_manager.load(profile_name)

            self.gesture_map = (
                self.profile_manager.get_gesture_map()
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

            # =================================================
            # CUSTOM STUDIO MODE
            # =================================================

            if self.custom_studio is not None:

                events = self.custom_studio.get(
                    "events",
                    []
                )

                for event in events:

                    event_gesture = event.get(
                        "gesture",
                        ""
                    )

                    if (
                        event_gesture
                        == confirmed_gesture
                    ):

                        print(
                            "🎯 Custom event matched:",
                            event.get("name")
                        )

                        self.custom_event_detected.emit(
                            event
                        )

                        break

                continue

            # =================================================
            # NORMAL PROFILE MODE
            # =================================================

            action = self.gesture_map.get(
                confirmed_gesture
            )

            if action:

                self.action_detected.emit(
                    action
                )

    @Slot()
    def stop(self):

        self._stop_requested = True
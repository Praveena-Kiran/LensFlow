import cv2

from PySide6.QtCore import QObject, Signal, Slot

from backend.gestures.google_gesture_recognizer import GoogleGestureRecognizer
from backend.gestures.gesture_stabilizer import GestureStabilizer
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

    def __init__(
        self,
        profile_name="presentation",
        custom_studio=None
    ):
        super().__init__()

        self.profile_name = profile_name
        self.custom_studio = custom_studio
        self.running = False

        self.stabilizer = GestureStabilizer()
        self.recognizer = GoogleGestureRecognizer()

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

    @Slot()
    def run(self):

        self.running = True

        camera = cv2.VideoCapture(0)

        if not camera.isOpened():

            self.error.emit(
                "Could not open webcam."
            )

            self.running = False
            return

        self.status_changed.emit("READY")

        while self.running:

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

        camera.release()

        self.status_changed.emit(
            "STOPPED"
        )

    @Slot()
    def stop(self):

        self.running = False
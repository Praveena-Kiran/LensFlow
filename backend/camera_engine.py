import cv2

from backend.gestures.google_gesture_recognizer import GoogleGestureRecognizer
from backend.gestures.gesture_stabilizer import GestureStabilizer
from backend.automation.action_manager import ActionManager
from backend.profile_manager import ProfileManager


class CameraEngine:

    def __init__(self):

        self.camera = None

        self.recognizer = GoogleGestureRecognizer()
        self.stabilizer = GestureStabilizer()
        self.action_manager = ActionManager()

        self.profile_manager = ProfileManager()
        self.profile_manager.load("coding")

        self.gesture_map = self.profile_manager.get_gesture_map()

    def start(self):

        self.camera = cv2.VideoCapture(0)

        if not self.camera.isOpened():
            raise RuntimeError("❌ Could not open webcam.")

        print("✅ Camera Started")

    def read(self):

        if self.camera is None:
            return None

        success, frame = self.camera.read()

        if not success:
            return None

        # Mirror effect
        frame = cv2.flip(frame, 1)

        # Detect gesture
        gesture = self.recognizer.detect(frame)

        # Stabilize gesture
        confirmed = self.stabilizer.update(gesture)

        if confirmed:

            action = self.gesture_map.get(confirmed)

            if action:
                self.action_manager.execute(
                    confirmed,
                    action
                )

        return frame

    def stop(self):

        if self.camera:

            self.camera.release()
            self.camera = None

        print("🛑 Camera Stopped")
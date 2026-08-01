import cv2
import mediapipe as mp

from backend.config.settings import *
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

        self.mp_hands = mp.solutions.hands

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=MAX_HANDS,
            min_detection_confidence=DETECTION_CONFIDENCE,
            min_tracking_confidence=TRACKING_CONFIDENCE
        )

        self.drawer = mp.solutions.drawing_utils

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

        frame = cv2.flip(frame, 1)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = self.hands.process(rgb)
        gesture = self.recognizer.detect(frame)

        if results.multi_hand_landmarks:

            for hand in results.multi_hand_landmarks:

                self.drawer.draw_landmarks(
                    frame,
                    hand,
                    self.mp_hands.HAND_CONNECTIONS
                )
                
                print("Detected:", gesture)

                confirmed = self.stabilizer.update(gesture)

                if confirmed:

                    print(f"✅ {confirmed}")

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
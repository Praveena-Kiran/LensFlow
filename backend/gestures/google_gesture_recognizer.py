import os

import cv2
import mediapipe as mp

from backend.paths import model_path as bundled_model_path


# MediaPipe category name -> name shown in Wield.
BUILTIN_GESTURES = {
    "Thumb_Up": "👍 Thumbs Up",
    "Thumb_Down": "👎 Thumbs Down",
    "Open_Palm": "✋ Open Palm",
    "Closed_Fist": "✊ Fist",
    "Victory": "✌️ Peace",
    "Pointing_Up": "☝️ Pointing Up",
}

BUILTIN_GESTURE_NAMES = list(BUILTIN_GESTURES.values())


class GoogleGestureRecognizer:

    def __init__(self):

        model_path = bundled_model_path("gesture_recognizer.task")

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Gesture model not found at {model_path}"
            )

        BaseOptions = mp.tasks.BaseOptions 
        GestureRecognizer = mp.tasks.vision.GestureRecognizer 
        GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions 
        VisionRunningMode = mp.tasks.vision.RunningMode

        with open(model_path, "rb") as f:
            model_buffer = f.read()

        options = GestureRecognizerOptions(
            base_options=BaseOptions(
                model_asset_buffer=model_buffer
            ),
            running_mode=VisionRunningMode.IMAGE
        )

        self.recognizer = GestureRecognizer.create_from_options(options)

        self.last_landmarks = None
        self.last_image_landmarks = None
        self.last_handedness = None

    def detect(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        result = self.recognizer.recognize(mp_image)

        # Keep the landmarks from this frame so custom gestures can be
        # matched without running MediaPipe a second time.
        self.last_landmarks = None
        self.last_image_landmarks = None
        self.last_handedness = None

        if result.hand_world_landmarks:
            self.last_landmarks = result.hand_world_landmarks[0]

        if result.hand_landmarks:
            self.last_image_landmarks = result.hand_landmarks[0]

        if result.handedness:
            self.last_handedness = result.handedness[0][0].category_name

        if result.gestures:

            gesture = result.gestures[0][0].category_name
            confidence = result.gestures[0][0].score

            return BUILTIN_GESTURES.get(gesture), confidence

        return None, 0.0

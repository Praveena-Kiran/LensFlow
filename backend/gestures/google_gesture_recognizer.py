import os
import sys

import cv2
import mediapipe as mp


def _model_path():
    """Locate the bundled gesture model, both from source and from a PyInstaller build."""
    base = getattr(sys, "_MEIPASS", None) or os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    return os.path.join(base, "backend", "models", "gesture_recognizer.task")


class GoogleGestureRecognizer:

    def __init__(self):

        model_path = _model_path()

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

    def detect(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        result = self.recognizer.recognize(mp_image)

        mapping = {
            "Thumb_Up": "👍 Thumbs Up",
            "Thumb_Down": "👎 Thumbs Down",
            "Open_Palm": "✋ Open Palm",
            "Closed_Fist": "✊ Fist",
            "Victory": "✌️ Peace",
            "Pointing_Up": "☝️ Pointing Up"
        }

        if result.gestures:

            gesture = result.gestures[0][0].category_name
            confidence = result.gestures[0][0].score

            return mapping.get(gesture), confidence

        return None, 0.0

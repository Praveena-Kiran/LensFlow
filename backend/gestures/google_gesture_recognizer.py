from backend import gesture_ai
import os
import cv2
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class GoogleGestureRecognizer:

    def __init__(self):

        model_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "models",
            "gesture_recognizer.task"
        )

        BaseOptions = python.BaseOptions
        GestureRecognizer = vision.GestureRecognizer
        GestureRecognizerOptions = vision.GestureRecognizerOptions
        VisionRunningMode = vision.RunningMode

        options = GestureRecognizerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
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

        if result.gestures:

            gesture = result.gestures[0][0].category_name

            mapping = {
                "Thumb_Up": "👍 Thumbs Up",
                "Thumb_Down": "👎 Thumbs Down",
                "Open_Palm": "✋ Open Palm",
                "Closed_Fist": "✊ Fist",
                "Victory": "✌️ Peace",
                "Pointing_Up": "☝️ Pointing Up"
            }

            return mapping.get(gesture)

        return None
import os
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import cv2

class GestureAI:

    def __init__(self):
        self.timestamp_ms = 0
        model_path = os.path.join(
        os.path.dirname(__file__),
            "models",
            "gesture_recognizer.task"
        )

        base_options = python.BaseOptions(
        model_asset_path=model_path
        )
        options = vision.GestureRecognizerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
        num_hands=1
        )
        self.recognizer = vision.GestureRecognizer.create_from_options(
            options
        )

    def detect(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )
        self.timestamp_ms += 33
        result = self.recognizer.recognize_for_video(
            image,
            self.timestamp_ms
        )
        if not result.gestures:
            return None

        gesture = result.gestures[0][0]
        gesture_name = gesture.category_name
        confidence = gesture.score
        print(f"Google: {gesture_name} ({confidence:.2f})")
        #if confidence < 0.80:
           # return None

        return gesture_name,confidence

       
        
        
    



    
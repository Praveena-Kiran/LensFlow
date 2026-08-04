import os
print("Current working directory:", os.getcwd())
import cv2
import mediapipe as mp




class GoogleGestureRecognizer:

    def __init__(self):

        print("GoogleGestureRecognizer created!")

        import traceback
        traceback.print_stack(limit=5)

        model_path = r"C:\\Users\\Praveena\\OneDrive\\Desktop\\LensFlow\\LensFlow\\backend\\models\\gesture_recognizer.task"

        print("MODEL =", model_path)
        print("repr  =", repr(model_path))

        print("MODEL PATH =", model_path)
        print("EXISTS =", os.path.exists(model_path))

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
        
        print("MODEL PATH =", model_path)
        print("ABSOLUTE =", os.path.isabs(model_path))
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
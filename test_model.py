from mediapipe.tasks import python
from mediapipe.tasks.python import vision

model_path = r"C:\\Users\\Praveena\\OneDrive\\Desktop\\LensFlow\\LensFlow\\backend\\models\\gesture_recognizer.task"

BaseOptions = python.BaseOptions

options = vision.GestureRecognizerOptions(
    base_options=BaseOptions(model_asset_path=model_path),
    running_mode=vision.RunningMode.IMAGE
)

recognizer = vision.GestureRecognizer.create_from_options(options)

print("SUCCESS!")
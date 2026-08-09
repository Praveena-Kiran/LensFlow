import cv2
from backend.camera_engine import CameraEngine

engine = CameraEngine()
engine.start()

try:
    while True:
        frame = engine.read()

        if frame is not None:
            cv2.imshow("LensFlow Presentation Camera", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    engine.stop()
    cv2.destroyAllWindows()
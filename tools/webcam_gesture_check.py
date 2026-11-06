"""Manual webcam check: shows the recognised gesture live. Run from the repo root:
    python -m tools.webcam_gesture_check
Press q to quit."""
import cv2
from backend.gestures.google_gesture_recognizer import GoogleGestureRecognizer

recognizer = GoogleGestureRecognizer()

camera = cv2.VideoCapture(0)

while True:

    success, frame = camera.read()

    if not success:
        break

    frame = cv2.flip(frame, 1)

    gesture, confidence = recognizer.detect(frame)

    if gesture:
        print(f"{gesture} ({confidence:.2f})")

        cv2.putText(
            frame,
            gesture,
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

    cv2.imshow("Google Gesture Test", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()
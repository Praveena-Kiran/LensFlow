import cv2
from backend.gestures.google_gesture_recognizer import GoogleGestureRecognizer

recognizer = GoogleGestureRecognizer()

camera = cv2.VideoCapture(0)

while True:

    success, frame = camera.read()

    if not success:
        break

    frame = cv2.flip(frame, 1)

    gesture = recognizer.detect(frame)

    if gesture:
        print(gesture)

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
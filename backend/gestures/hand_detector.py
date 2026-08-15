import cv2

from backend.automation.action_manager import ActionManager
from backend.gestures.google_gesture_recognizer import GoogleGestureRecognizer
from backend.gestures.gesture_stabilizer import GestureStabilizer
from backend.profile_manager import ProfileManager


ACTION_NAMES = {
    "presentation_start": "Start Presentation",
    "presentation_end": "End Presentation",
    "presentation_next": "Next Slide",
    "presentation_previous": "Previous Slide",
    "ACTIVATE": "Activate LensFlow",
    "DEACTIVATE": "Deactivate LensFlow",
}


def start_hand_detection(profile_name="presentation"):

    # -----------------------------
    # Managers
    # -----------------------------

    stabilizer = GestureStabilizer()
    action_manager = ActionManager()

    profile_manager = ProfileManager()
    profile_manager.load(profile_name)

    gesture_map = profile_manager.get_gesture_map()

    # -----------------------------
    # Camera + Recognizer
    # -----------------------------

    camera = cv2.VideoCapture(0)
    recognizer = GoogleGestureRecognizer()

    if not camera.isOpened():
        print("❌ Could not open webcam.")
        return

    print("✅ Hand Detection Started")
    print(f"🎯 Profile: {profile_name}")
    print("Press Q to quit.")

    # -----------------------------
    # UI state
    # -----------------------------

    current_gesture = "None"
    current_action = "None"

    studio_name = profile_name.title() + " Studio"

    # -----------------------------
    # Detection loop
    # -----------------------------

    while True:

        success, frame = camera.read()

        if not success:
            break

        # Mirror effect
        frame = cv2.flip(frame, 1)

        # -----------------------------
        # Gesture Recognition
        # -----------------------------

        gesture, confidence = recognizer.detect(frame)

        # -----------------------------
        # Gesture Stabilization
        # -----------------------------

        confirmed_gesture = stabilizer.update(
            gesture,
            confidence
        )

        if confirmed_gesture:

            current_gesture = confirmed_gesture

            action = gesture_map.get(
                confirmed_gesture
            )

            if action:

                current_action = action

                action_manager.execute(
                    confirmed_gesture,
                    action
                )

        # -----------------------------
        # UI Panel
        # -----------------------------

        cv2.rectangle(
            frame,
            (10, 10),
            (430, 200),
            (35, 35, 35),
            -1
        )

        # -----------------------------
        # Title
        # -----------------------------

        cv2.putText(
            frame,
            "LensFlow",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (255, 255, 255),
            3
        )

        # -----------------------------
        # Studio
        # -----------------------------

        cv2.putText(
            frame,
            f"Studio : {studio_name}",
            (20, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        # -----------------------------
        # Status
        # -----------------------------

        status = action_manager.status

        status_color = (
            (0, 255, 0)
            if status == "PRESENTING"
            else (255, 255, 255)
        )

        cv2.putText(
            frame,
            f"Status : {status}",
            (20, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            status_color,
            2
        )

        # -----------------------------
        # Gesture
        # -----------------------------

        cv2.putText(
            frame,
            f"Gesture : {current_gesture}",
            (20, 145),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        # -----------------------------
        # Action
        # -----------------------------

        display_action = ACTION_NAMES.get(
            current_action,
            current_action
        )

        cv2.putText(
            frame,
            f"Action : {display_action}",
            (20, 180),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        # -----------------------------
        # Show Window
        # -----------------------------

        cv2.imshow(
            "LensFlow - Hand Detection",
            frame
        )

        # -----------------------------
        # Quit
        # -----------------------------

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # -----------------------------
    # Cleanup
    # -----------------------------

    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    start_hand_detection("presentation")
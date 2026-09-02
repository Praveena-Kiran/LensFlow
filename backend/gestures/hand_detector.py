import cv2

from backend.automation.action_manager import ActionManager
from backend.gestures.google_gesture_recognizer import GoogleGestureRecognizer
from backend.gestures.gesture_stabilizer import GestureStabilizer
from backend.profile_manager import ProfileManager


# ---------------------------------------------------------
# Global objects
# ---------------------------------------------------------

stabilizer = GestureStabilizer()
action_manager = ActionManager()
profile_manager = ProfileManager()


# ---------------------------------------------------------
# Display names for actions
# ---------------------------------------------------------

ACTION_NAMES = {
    "presentation_start": "Start Presentation",
    "presentation_end": "End Presentation",
    "presentation_next": "Next Slide",
    "presentation_previous": "Previous Slide",
    "ACTIVATE": "Activate LensFlow",
    "DEACTIVATE": "Deactivate LensFlow",
}


# ---------------------------------------------------------
# Hand detection
# ---------------------------------------------------------

def start_hand_detection(profile_name="presentation"):

    # -----------------------------------------------------
    # Load profile
    # -----------------------------------------------------

    if not profile_manager.load(profile_name):
        print(f"❌ Could not load profile: {profile_name}")
        return

    gesture_map = profile_manager.get_gesture_map()

    print(f"[OK] Loaded profile: {profile_name}")

    # -----------------------------------------------------
    # LensFlow state
    # -----------------------------------------------------

    lensflow_active = False

    # -----------------------------------------------------
    # Camera
    # -----------------------------------------------------

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("❌ Could not open webcam.")
        return

    recognizer = GoogleGestureRecognizer()

    print("✅ Hand Detection Started")
    print("Press Q to quit.")

    # -----------------------------------------------------
    # UI state
    # -----------------------------------------------------

    current_gesture = "None"
    current_action = "None"

    studio_name = profile_name.title()

    # -----------------------------------------------------
    # Main loop
    # -----------------------------------------------------

    while True:

        success, frame = camera.read()

        if not success:
            break

        # Mirror camera
        frame = cv2.flip(frame, 1)

        # -------------------------------------------------
        # Gesture recognition
        # -------------------------------------------------

        gesture, confidence = recognizer.detect(frame)

        # Stabilize gesture
        confirmed_gesture = stabilizer.update(
            gesture,
            confidence
        )

        # -------------------------------------------------
        # Process confirmed gesture
        # -------------------------------------------------

        if confirmed_gesture:

            current_gesture = confirmed_gesture

            # -------------------------------------------------
            # Activation
            # -------------------------------------------------

            if confirmed_gesture == "Open_Palm":

                if not lensflow_active:

                    lensflow_active = True
                    current_action = "ACTIVATE"

                    print("🟢 LensFlow ACTIVATED")

                # Do NOT execute the presentation action
                # associated with Open_Palm.
                continue

            # -------------------------------------------------
            # Normal gesture processing
            # -------------------------------------------------

            if lensflow_active:

                action = gesture_map.get(
                    confirmed_gesture
                )

                if action:

                    current_action = action

                    action_manager.execute(
                        confirmed_gesture,
                        action
                    )

        # -------------------------------------------------
        # Camera UI panel
        # -------------------------------------------------

        cv2.rectangle(
            frame,
            (10, 10),
            (460, 215),
            (35, 35, 35),
            -1
        )

        # -------------------------------------------------
        # Title
        # -------------------------------------------------

        cv2.putText(
            frame,
            "LensFlow",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (255, 255, 255),
            3
        )

        # -------------------------------------------------
        # Studio
        # -------------------------------------------------

        cv2.putText(
            frame,
            f"Studio : {studio_name}",
            (20, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        # -------------------------------------------------
        # LensFlow status
        # -------------------------------------------------

        if lensflow_active:

            status = "ACTIVE"
            status_color = (0, 255, 0)

        else:

            status = "READY"
            status_color = (180, 180, 180)

        cv2.putText(
            frame,
            f"Status : {status}",
            (20, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            status_color,
            2
        )

        # -------------------------------------------------
        # Gesture
        # -------------------------------------------------

        cv2.putText(
            frame,
            f"Gesture : {current_gesture}",
            (20, 145),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        # -------------------------------------------------
        # Action
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Show camera
        # -------------------------------------------------

        cv2.imshow(
            "LensFlow - Hand Detection",
            frame
        )

        # -------------------------------------------------
        # Quit
        # -------------------------------------------------

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # -----------------------------------------------------
    # Cleanup
    # -----------------------------------------------------

    camera.release()
    cv2.destroyAllWindows()


# ---------------------------------------------------------
# Direct execution
# ---------------------------------------------------------

if __name__ == "__main__":
    start_hand_detection()
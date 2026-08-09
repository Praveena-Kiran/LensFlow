import os
import json
import cv2

from backend.automation.action_manager import ActionManager
from backend.gestures.google_gesture_recognizer import GoogleGestureRecognizer
from backend.gestures.gesture_stabilizer import GestureStabilizer
from backend.profile_manager import ProfileManager


stabilizer = GestureStabilizer()
action_manager = ActionManager()

profile_manager = ProfileManager()
profile_manager.load("coding")

gesture_map = profile_manager.get_gesture_map()

ACTION_NAMES = {
    "presentation_start": "Start Presentation",
    "presentation_end": "End Presentation",
    "presentation_next": "Next Slide",
    "presentation_previous": "Previous Slide",
    "ACTIVATE": "Activate LensFlow",
    "DEACTIVATE": "Deactivate LensFlow"
}

with open("backend/config/gesture_map.json", "r", encoding="utf-8") as file:
    gesture_map = json.load(file)


def start_hand_detection():

    camera = cv2.VideoCapture(0)
    recognizer = GoogleGestureRecognizer()

    if not camera.isOpened():
        print("❌ Could not open webcam.")
        return

    print("✅ Hand Detection Started")
    print("Press Q to quit.")

    current_gesture = "None"
    current_action = "None"
    studio_name = "Presentation Studio"

    while True:

        success, frame = camera.read()

        if not success:
            break

        # Mirror effect
        frame = cv2.flip(frame, 1)


        # MediaPipe Gesture Recognizer
        gesture, confidence = recognizer.detect(frame)

      #  print("Detected:", gesture)


        # Stabilize gesture
        confirmed_gesture = stabilizer.update(gesture, confidence)


        if confirmed_gesture:

            current_gesture = confirmed_gesture

            action = gesture_map.get(confirmed_gesture)


            if action:

                current_action = action

               # print(
                #    f"Executing {confirmed_gesture} -> {action}"
                #)

                action_manager.execute(
                    confirmed_gesture,
                    action
                )


        # UI Panel
        cv2.rectangle(
        frame,
        (10, 10),
        (430, 200),
        (35, 35, 35),
        -1
    )


        # Title
        cv2.putText(
            frame,
            "LensFlow",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (255,255,255),
            3
        )

        cv2.putText(
            frame,
            f"Studio : {studio_name}",
            (20, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255,255,255),
            2
        )



        # Status
        status = (
            "ACTIVE"
            if action_manager.active
            else "INACTIVE"
        )


        status_color = (
        (0,255,0)
        if action_manager.active
        else (0,0,255)
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


        # Gesture display
        cv2.putText(
            frame,
            f"Gesture : {current_gesture}",
            (20,145),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255,255,255),
            2
        )

        
        

        # Action display
        display_action = ACTION_NAMES.get(
        current_action,
        current_action
        )


        cv2.putText(
            frame,
            f"Action : {display_action}",
            (20,180),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255,255,255),
            2
        )


        cv2.imshow(
            "LensFlow - Hand Detection",
            frame
        )


        if cv2.waitKey(1) & 0xFF == ord("q"):
            break



    camera.release()
    cv2.destroyAllWindows()



if __name__ == "__main__":
    start_hand_detection()
from mediapipe import framework
import os
from backend.automation import action_manager
import json
from backend.automation.action_manager import ActionManager
import cv2
import mediapipe as mp
from backend.gestures.gesture_recognizer import GestureRecognizer
from backend.gestures.gesture_stabilizer import GestureStabilizer
from backend.profile_manager import ProfileManager
from backend.config.settings import *
mp_hands = mp.solutions.hands

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=MAX_HANDS,
    min_detection_confidence=DETECTION_CONFIDENCE,
    min_tracking_confidence=TRACKING_CONFIDENCE
)

# Utility for drawing landmarks
mp_draw = mp.solutions.drawing_utils
recognizer = GestureRecognizer()
stabilizer = GestureStabilizer()
action_manager = ActionManager()
profile_manager = ProfileManager()
profile_manager.load("coding")
gesture_map = profile_manager.get_gesture_map()

with open("backend/config/gesture_map.json", "r", encoding="utf-8") as file:
    gesture_map = json.load(file)

def start_hand_detection():
    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("❌ Could not open webcam.")
        return

    print("✅ Hand Detection Started")
    print("Press Q to quit.")

    current_gesture = "None"
    current_action = "None"

    while True:
        success, frame = camera.read()

        if not success:
            break

        # Flip image for a mirror effect
        frame = cv2.flip(frame, 1)

        # Convert BGR → RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detect hands
        results = hands.process(rgb_frame)

        # Draw landmarks
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:

                mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS
                )

                
                gesture = recognizer.detect(hand_landmarks)

                confirmed_gesture = stabilizer.update(gesture)

                display_text = "Detecting..."

                if confirmed_gesture and confirmed_gesture != current_gesture:

                    current_gesture = confirmed_gesture

                    action = gesture_map.get(confirmed_gesture)

                    if action:
                        current_action = action
                        action_manager.execute(confirmed_gesture, action)

                    display_text = f"Confirmed: {confirmed_gesture}"


               

                display_action = "None"

                if current_action != "None":
                    display_action = os.path.splitext(os.path.basename(current_action))[0]

                cv2.putText(
                    frame,
                    f"Action : {display_action}",
                    (20,130),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255,255,255),
                    2
                )


            # Background panel
        cv2.rectangle(frame, (10, 10), (380, 170), (40, 40, 40), -1)

        # Title
        cv2.putText(
            frame,
            "LensFlow",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

        # Status
        status = "ACTIVE" if action_manager.active else "INACTIVE"
        status_color = (0, 255, 0) if action_manager.active else (0, 0, 255)

        cv2.putText(
            frame,
            f"Status : {status}",
            (20, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            status_color,
            2
        )

        # Gesture
        cv2.putText(
            frame,
            f"Gesture : {current_gesture}",
            (20, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255,255,255),
            2
        )

        # Action
        display_action = "None"

        if current_action != "None":
            display_action = os.path.splitext(os.path.basename(current_action))[0]

        cv2.putText(
            frame,
            f"Action : {display_action}",
            (20, 130),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )
     

        cv2.imshow("LensFlow - Hand Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    start_hand_detection()
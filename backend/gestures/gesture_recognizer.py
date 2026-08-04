import mediapipe as mp


class GestureRecognizer:

    def __init__(self):
        self.mp_hands = mp.solutions.hands

    # ----------------------------
    # Finger helpers
    # ----------------------------

    def finger_extended(self, tip, pip, landmarks):
        return landmarks[tip].y < landmarks[pip].y

    def thumb_extended(self, landmarks):
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        thumb_mcp = landmarks[2]

        return (
            abs(thumb_tip.x - thumb_mcp.x) >
            abs(thumb_ip.x - thumb_mcp.x)
        )
            

    # ----------------------------
    # Gestures
    # ----------------------------

    def is_open_palm(self, landmarks):

        return (
            self.thumb_extended(landmarks)
            and self.finger_extended(8, 6, landmarks)
            and self.finger_extended(12, 10, landmarks)
            and self.finger_extended(16, 14, landmarks)
            and self.finger_extended(20, 18, landmarks)
        )


    def is_thumbs_up(self, landmarks):

        thumb = self.thumb_extended(landmarks)

        index = self.finger_extended(8, 6, landmarks)
        middle = self.finger_extended(12, 10, landmarks)
        ring = self.finger_extended(16, 14, landmarks)
        pinky = self.finger_extended(20, 18, landmarks)

        thumb_tip = landmarks[4]
        thumb_mcp = landmarks[2]
        index_mcp = landmarks[5]
        wrist = landmarks[0]

        print("Thumb Tip :", thumb_tip.x, thumb_tip.y)
        print("Thumb MCP :", thumb_mcp.x, thumb_mcp.y)
        print("Index MCP :", index_mcp.x, index_mcp.y)
        print("Wrist     :", wrist.x, wrist.y)
        print("----------------")
        return (
            thumb
            and thumb_tip.y < index_mcp.y - 0.06
            and not index
            and not middle
            and not ring
            and not pinky
        )


    def is_peace(self, landmarks):

        return (
            self.finger_extended(8, 6, landmarks)
            and self.finger_extended(12, 10, landmarks)
            and not self.finger_extended(16, 14, landmarks)
            and not self.finger_extended(20, 18, landmarks)
        )


    def is_fist(self, landmarks):

        return (
            not self.finger_extended(8, 6, landmarks)
            and not self.finger_extended(12, 10, landmarks)
            and not self.finger_extended(16, 14, landmarks)
            and not self.finger_extended(20, 18, landmarks)
            and not self.thumb_extended(landmarks)
        )


    # ----------------------------
    # Main detector
    # ----------------------------

    def detect(self, hand_landmarks):

        landmarks = hand_landmarks.landmark

        # Order matters!

        if self.is_open_palm(landmarks):
            return "✋ Open Palm"

        if self.is_thumbs_up(landmarks):
            return "👍 Thumbs Up"

        if self.is_peace(landmarks):
            return "✌️ Peace"

        if self.is_fist(landmarks):
            return "✊ Fist"

        return None
        
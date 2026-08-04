class GestureStabilizer:

    def __init__(self, required_frames=5):
        self.required_frames = required_frames
        self.last_gesture = None
        self.frame_count = 0
        self.triggered = False

    def update(self, current_gesture):

        # No hand detected
        if current_gesture is None:
            self.last_gesture = None
            self.frame_count = 0
            self.triggered = False
            return None


        # Same gesture
        if current_gesture == self.last_gesture:
            self.frame_count += 1

        # New gesture
        else:
            self.last_gesture = current_gesture
            self.frame_count = 1
            self.triggered = False


        # Confirm only once
        if self.frame_count >= self.required_frames:

            if not self.triggered:
                self.triggered = True
                return current_gesture


        return None
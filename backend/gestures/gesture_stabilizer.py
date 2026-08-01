class GestureStabilizer:

    def __init__(self, required_frames=5):
        self.required_frames = required_frames
        self.last_gesture = None
        self.frame_count = 0

    def update(self, current_gesture):

        if current_gesture == self.last_gesture:
            self.frame_count += 1
        else:
            self.last_gesture = current_gesture
            self.frame_count = 1

        if self.frame_count >= self.required_frames:
            return current_gesture

        return None
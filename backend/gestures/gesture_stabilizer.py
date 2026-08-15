from collections import deque


class GestureStabilizer:

    def __init__(
        self,
        required_detections=1,
        window_size=3,
        confidence_threshold=0.60
    ):
        self.required_detections = required_detections
        self.window_size = window_size
        self.confidence_threshold = confidence_threshold

        self.detections = deque(maxlen=window_size)
        self.triggered_gesture = None

    def update(self, current_gesture, confidence):

        # Ignore low-confidence detections
        if current_gesture is None or confidence < self.confidence_threshold:
            self.detections.append(None)
            return None

        self.detections.append(current_gesture)

        # Only trigger when this is a new gesture
        if current_gesture != self.triggered_gesture:

            recent_same_gesture = sum(
                1
                for detection in self.detections
                if detection == current_gesture
            )

            if recent_same_gesture >= self.required_detections:

                self.triggered_gesture = current_gesture
                return current_gesture

        return None
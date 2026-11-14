import time
from collections import deque


class GestureStabilizer:
    """
    Turns per-frame detections into single triggers.

    - A gesture triggers once, then not again until the hand has relaxed
      (no gesture for a full window).
    - With hold_time > 0 the same gesture must be seen continuously for that
      many seconds first (an accessibility option: avoids triggers from
      passing hand shapes, at the cost of being slower).
    """

    def __init__(
        self,
        required_detections=1,
        window_size=3,
        confidence_threshold=0.60,
        hold_time=0.0,
        clock=time.monotonic,
    ):
        self.required_detections = required_detections
        self.window_size = window_size
        self.confidence_threshold = confidence_threshold
        self.hold_time = hold_time
        self.clock = clock

        self.detections = deque(maxlen=window_size)
        self.triggered_gesture = None

        # The gesture currently being held and since when (for hold_time).
        self._holding = None
        self._holding_since = 0.0

    def update(self, current_gesture, confidence):

        now = self.clock()

        # Ignore low-confidence detections
        if current_gesture is None or confidence < self.confidence_threshold:
            self.detections.append(None)
            self._holding = None

            # Once the hand has been relaxed / out of view for a full window,
            # allow the same gesture to trigger again (e.g. two "next slide"
            # thumbs-ups in a row).
            if all(d is None for d in self.detections):
                self.triggered_gesture = None

            return None

        self.detections.append(current_gesture)

        if current_gesture != self._holding:
            self._holding = current_gesture
            self._holding_since = now

        # Only trigger when this is a new gesture
        if current_gesture != self.triggered_gesture:

            recent_same_gesture = sum(
                1
                for detection in self.detections
                if detection == current_gesture
            )

            # (tiny tolerance so 0.3 s held does not fail on float rounding)
            held_long_enough = now - self._holding_since >= self.hold_time - 1e-6

            if recent_same_gesture >= self.required_detections and held_long_enough:

                self.triggered_gesture = current_gesture
                return current_gesture

        return None

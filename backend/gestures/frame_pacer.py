"""
Limits how often camera frames are processed, to keep CPU use (and laptop
fans) down. Hand tracking runs on every processed frame, which is the
expensive part.

    no hand in view  -> IDLE_FPS   (enough to notice a hand arriving)
    hand in view     -> ACTIVE_FPS (smooth gestures and motions)
"""

import time


IDLE_FPS = 10
ACTIVE_FPS = 24


class FramePacer:

    def __init__(self, idle_fps=IDLE_FPS, active_fps=ACTIVE_FPS, clock=time.monotonic, sleep=time.sleep):
        self.idle_interval = 1.0 / idle_fps
        self.active_interval = 1.0 / active_fps
        self.clock = clock
        self.sleep = sleep
        self._last = None

    def wait(self, hand_present):
        """Call once per loop, after processing a frame."""

        now = self.clock()

        if self._last is not None:
            interval = self.active_interval if hand_present else self.idle_interval
            remaining = interval - (now - self._last)
            if remaining > 0:
                self.sleep(remaining)
                now = self.clock()

        self._last = now

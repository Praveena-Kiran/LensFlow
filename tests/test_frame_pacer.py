import unittest

from backend.gestures.frame_pacer import FramePacer


class FakeTime:
    def __init__(self):
        self.now = 0.0
        self.slept = []

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.slept.append(round(seconds, 4))
        self.now += seconds


class FramePacerTests(unittest.TestCase):

    def test_idle_and_active_rates(self):
        t = FakeTime()
        p = FramePacer(idle_fps=10, active_fps=25, clock=t.clock, sleep=t.sleep)
        p.wait(False)                 # first frame: no wait
        t.now += 0.02                 # 20 ms of processing
        p.wait(False)                 # idle: wait to 100 ms
        t.now += 0.02
        p.wait(True)                  # active: wait to 40 ms
        self.assertEqual(t.slept, [0.08, 0.02])

    def test_no_wait_when_processing_is_slow(self):
        t = FakeTime()
        p = FramePacer(clock=t.clock, sleep=t.sleep)
        p.wait(True)
        t.now += 0.5
        p.wait(False)
        self.assertEqual(t.slept, [])


if __name__ == "__main__":
    unittest.main()

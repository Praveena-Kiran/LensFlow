"""
Soft sound cues, so people know what Wield did without looking at it
(e.g. while a slideshow fills the screen, or for people with low vision).

    armed     rising two-note chime   Wield is now listening for a command
    action    single short note       an action ran
    disarmed  falling two-note chime  Wield stopped listening
    error     low note                something didn't work

The tones are generated once as small WAV files in the user's data
folder (no audio assets to ship) and played asynchronously with
Windows' built-in winsound. On other systems they are silently skipped.
"""

import math
import os
import struct
import time
import wave

from backend.paths import user_data_dir

SAMPLE_RATE = 22050
VOLUME = 0.22          # quiet: these should never startle anyone
FADE = 0.012           # seconds of fade in/out (avoids clicks)

# name -> [(frequency Hz, seconds), ...]
CUES = {
    "armed": [(660, 0.07), (880, 0.10)],
    "action": [(988, 0.09)],
    "disarmed": [(660, 0.07), (494, 0.10)],
    "error": [(247, 0.20)],
}

MIN_GAP = 0.12  # seconds between two plays of the same cue


def tone_frames(notes, rate=SAMPLE_RATE, volume=VOLUME, fade=FADE):
    """16-bit mono PCM bytes for a list of (frequency, seconds) notes."""
    frames = bytearray()
    fade_n = max(1, int(fade * rate))
    for frequency, seconds in notes:
        n = int(seconds * rate)
        for i in range(n):
            envelope = min(1.0, i / fade_n, (n - 1 - i) / fade_n)
            value = volume * envelope * math.sin(2 * math.pi * frequency * i / rate)
            frames += struct.pack("<h", int(value * 32767))
        frames += b"\x00\x00" * int(0.015 * rate)  # tiny gap between notes
    return bytes(frames)


def write_wav(path, notes):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(tone_frames(notes))


def _winsound_player(path):
    import winsound
    winsound.PlaySound(
        path,
        winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT,
    )


def default_player():
    try:
        import winsound  # noqa: F401  (Windows only)
    except ImportError:
        return None
    return _winsound_player


class SoundCues:

    def __init__(self, folder=None, player="default", clock=time.monotonic):
        self.folder = folder or os.path.join(user_data_dir(), "sounds")
        self.player = default_player() if player == "default" else player
        self.enabled = True
        self._clock = clock
        self._last = {}

    def path(self, cue):
        return os.path.join(self.folder, f"{cue}.wav")

    def ensure_files(self):
        os.makedirs(self.folder, exist_ok=True)
        for cue, notes in CUES.items():
            if not os.path.exists(self.path(cue)):
                write_wav(self.path(cue), notes)

    def play(self, cue):
        """Play a cue if sounds are on. Never raises."""
        if not self.enabled or self.player is None or cue not in CUES:
            return False

        now = self._clock()
        if now - self._last.get(cue, -1e9) < MIN_GAP:
            return False
        self._last[cue] = now

        try:
            self.ensure_files()
            self.player(self.path(cue))
            return True
        except Exception as e:
            print(f"⚠ Could not play sound '{cue}': {e}")
            return False

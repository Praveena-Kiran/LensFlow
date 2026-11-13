"""
Startup check used by the build pipeline: `Wield --self-test`.

Loads the bundled gesture model, runs one detection, checks the user data
folder is writable, the UI modules import, the voice engine's native
libraries load and the sound cues can be written. Exit code 0 means OK. Results
are also written to self_test.log in the user data folder, because the
packaged app has no console window.
"""

import os
import sys
import traceback


def run():

    lines = []
    ok = True

    def check(name, fn):
        nonlocal ok
        try:
            detail = fn()
            lines.append(f"OK    {name}" + (f": {detail}" if detail else ""))
        except Exception:
            ok = False
            lines.append(f"FAIL  {name}\n{traceback.format_exc()}")

    def model():
        import numpy as np
        from backend.gestures.google_gesture_recognizer import GoogleGestureRecognizer
        recognizer = GoogleGestureRecognizer()
        return str(recognizer.detect(np.zeros((240, 320, 3), np.uint8)))

    def data_dir():
        from backend.paths import user_config_path, user_data_dir
        user_config_path("studios.json")
        probe = os.path.join(user_data_dir(), ".write_test")
        with open(probe, "w") as f:
            f.write("ok")
        os.remove(probe)
        return user_data_dir()

    def ui():
        import main  # noqa: F401  (imports every page and component)
        from backend.paths import APP_DIR
        qss = os.path.join(APP_DIR, "frontend", "styles", "theme.qss")
        if not os.path.isfile(qss):
            raise FileNotFoundError(qss)

    def voice_engine():
        # Loads Vosk's native library and PortAudio (sounddevice) the way the
        # app does. Needs no microphone: CI machines don't have one.
        import vosk
        import sounddevice
        vosk.SetLogLevel(-1)
        if not hasattr(vosk, "KaldiRecognizer"):
            raise RuntimeError("vosk.KaldiRecognizer missing")
        return f"vosk ok, PortAudio {sounddevice.get_portaudio_version()[1]}"

    def sound_cues():
        from backend.feedback.sounds import CUES, SoundCues
        cues = SoundCues(player=None)
        cues.ensure_files()
        missing = [c for c in CUES if not os.path.isfile(cues.path(c))]
        if missing:
            raise FileNotFoundError(", ".join(missing))
        return f"{len(CUES)} sounds"

    check("gesture model", model)
    check("user data folder", data_dir)
    check("ui modules", ui)
    check("voice engine", voice_engine)
    check("sound cues", sound_cues)

    report = "\n".join(lines)
    print(report)

    try:
        from backend.paths import user_data_dir
        with open(os.path.join(user_data_dir(), "self_test.log"), "w", encoding="utf-8") as f:
            f.write(report + "\n")
    except Exception:
        pass

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())

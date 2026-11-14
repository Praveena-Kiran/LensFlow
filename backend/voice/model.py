"""
The offline speech model (Vosk, small English, ~40 MB).

It isn't shipped with Wield: the user downloads it once from Settings,
and it lives in the user's data folder. Recognition then runs entirely
on the computer; no audio is sent anywhere.
"""

import os
import shutil
import tempfile
import urllib.request
import zipfile

from backend.paths import user_data_dir

MODEL_NAME = "vosk-model-small-en-us-0.15"
MODEL_URL = f"https://alphacephei.com/vosk/models/{MODEL_NAME}.zip"
MODEL_SIZE_MB = 40


def model_dir():
    return os.path.join(user_data_dir(), "voice", MODEL_NAME)


def model_ready(path=None):
    """True if a usable model is installed (it has an 'am' and 'conf' folder)."""
    path = path or model_dir()
    return all(os.path.isdir(os.path.join(path, sub)) for sub in ("am", "conf"))


def vosk_available():
    try:
        import vosk  # noqa: F401
        import sounddevice  # noqa: F401
    except Exception:
        return False
    return True


def download_model(progress=None, url=MODEL_URL, target=None, opener=urllib.request.urlopen):
    """
    Download and unpack the model. `progress(done_bytes, total_bytes)` is
    called while downloading. Returns the model folder. Raises on failure,
    leaving no half-installed model behind.
    """
    target = target or model_dir()
    parent = os.path.dirname(target)
    os.makedirs(parent, exist_ok=True)

    with tempfile.TemporaryDirectory(dir=parent) as tmp:
        archive = os.path.join(tmp, "model.zip")

        with opener(url) as response, open(archive, "wb") as out:
            total = int(response.headers.get("Content-Length") or 0)
            done = 0
            while True:
                chunk = response.read(256 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                done += len(chunk)
                if progress:
                    progress(done, total)

        with zipfile.ZipFile(archive) as z:
            z.extractall(tmp)

        # The zip holds one top-level folder named like the model.
        extracted = os.path.join(tmp, os.path.basename(target))
        if not model_ready(extracted):
            candidates = [
                os.path.join(tmp, d) for d in os.listdir(tmp)
                if model_ready(os.path.join(tmp, d))
            ]
            if not candidates:
                raise RuntimeError("The download didn't contain a speech model.")
            extracted = candidates[0]

        if os.path.exists(target):
            shutil.rmtree(target)
        shutil.move(extracted, target)

    return target

"""
Listens to the microphone on a QThread and turns speech into voice
triggers ("🎤 next slide"), using an offline Vosk model restricted to the
studio's phrases (see commands.py).

Signals mirror the gesture worker so MainWindow can treat both alike.
"""

import json
import queue

from PySide6.QtCore import QObject, Signal, Slot

from backend.voice.commands import (
    VoiceCommandMatcher,
    average_confidence,
    grammar,
)
from backend.voice.model import model_dir, model_ready

SAMPLE_RATE = 16000
BLOCK_SIZE = 4000          # 0.25 s of audio per read


def _default_recognizer(phrases, wake_word):
    import vosk

    vosk.SetLogLevel(-1)
    model = vosk.Model(model_dir())
    recognizer = vosk.KaldiRecognizer(
        model, SAMPLE_RATE, json.dumps(grammar(phrases, wake_word))
    )
    recognizer.SetWords(True)
    return recognizer


def _default_stream(callback):
    import sounddevice

    return sounddevice.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        dtype="int16",
        channels=1,
        callback=lambda data, frames, t, status: callback(bytes(data)),
    )


class VoiceWorker(QObject):

    # A voice trigger was spoken, e.g. "🎤 next slide".
    command = Signal(str)
    # The wake phrase was heard on its own; waiting for a command.
    armed = Signal()
    # Every recognised utterance and what happened to it (for the log/UI).
    heard = Signal(str, str)
    status_changed = Signal(str)
    error = Signal(str)
    finished = Signal()

    def __init__(
        self,
        phrases,
        wake_word=True,
        recognizer_factory=_default_recognizer,
        stream_factory=_default_stream,
    ):
        super().__init__()
        self.phrases = list(phrases)
        self.wake_word = wake_word
        self.matcher = VoiceCommandMatcher(self.phrases, wake_word=wake_word)
        self._recognizer_factory = recognizer_factory
        self._stream_factory = stream_factory
        self._audio = queue.Queue()
        self._stop_requested = False

    @Slot()
    def run(self):
        try:
            self._run()
        finally:
            self.status_changed.emit("STOPPED")
            self.finished.emit()

    def _run(self):
        if self._recognizer_factory is _default_recognizer and not model_ready():
            self.error.emit(
                "Voice commands need the speech model. Download it in Settings."
            )
            return

        try:
            recognizer = self._recognizer_factory(self.phrases, self.wake_word)
            stream = self._stream_factory(self._audio.put)
        except Exception as e:
            self.error.emit(f"Couldn't start voice commands: {e}")
            return

        try:
            stream.start()
        except Exception as e:
            self.error.emit(
                f"Couldn't open the microphone ({e}). Check it's connected and "
                "that Windows allows apps to use it."
            )
            return

        self.status_changed.emit("LISTENING")

        try:
            while not self._stop_requested:
                try:
                    data = self._audio.get(timeout=0.3)
                except queue.Empty:
                    continue
                if recognizer.AcceptWaveform(data):
                    self._handle(json.loads(recognizer.Result() or "{}"))
            self._handle(json.loads(recognizer.FinalResult() or "{}"))
        finally:
            try:
                stream.stop()
                stream.close()
            except Exception:
                pass

    def _handle(self, result):
        text = (result or {}).get("text", "")
        event = self.matcher.process(text, average_confidence(result or {}))
        if event is None:
            return

        if event.kind == "command":
            print(f"[voice] heard “{event.text}” → {event.trigger}")
            self.heard.emit(event.text, "command")
            self.command.emit(event.trigger)
        elif event.kind == "armed":
            print(f"[voice] heard “{event.text}” → listening for a command")
            self.heard.emit(event.text, "armed")
            self.armed.emit()
        else:
            print(f"[voice] heard “{event.text}” → ignored ({event.reason})")
            self.heard.emit(event.text, event.reason)

    @Slot()
    def stop(self):
        self._stop_requested = True

    def feed_audio(self, data):
        """For tests: queue raw audio as if it came from the microphone."""
        self._audio.put(data)

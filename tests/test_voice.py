import io
import json
import os
import tempfile
import unittest
import zipfile
from unittest import mock

try:
    import PySide6  # noqa: F401
    HAVE_QT = True
except ImportError:  # CI's unit-test job installs only the standard library
    HAVE_QT = False

from backend.voice.commands import (
    UNKNOWN,
    VoiceCommandMatcher,
    average_confidence,
    check_phrase,
    grammar,
    is_voice_trigger,
    normalize_phrase,
    phrase_of,
    voice_trigger,
)

PHRASES = ["next slide", "go back"]


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


class PhraseTests(unittest.TestCase):

    def test_normalize_and_triggers(self):
        self.assertEqual(normalize_phrase("  Next, Slide! "), "next slide")
        self.assertEqual(voice_trigger("Next Slide"), "🎤 next slide")
        self.assertTrue(is_voice_trigger("🎤 next slide"))
        self.assertFalse(is_voice_trigger("👍 Thumbs Up"))
        self.assertEqual(phrase_of("🎤 next slide"), "next slide")
        self.assertIsNone(phrase_of("Swipe right"))

    def test_grammar_has_wake_variants_and_unknown(self):
        g = grammar(PHRASES, wake_word=True)
        self.assertIn("next slide", g)
        self.assertIn("hey wield next slide", g)
        self.assertIn("hey wield", g)
        self.assertEqual(g[-1], UNKNOWN)
        self.assertNotIn("hey wield", grammar(PHRASES, wake_word=False))

    def test_check_phrase(self):
        self.assertTrue(check_phrase("next one please")[0])
        self.assertFalse(check_phrase("")[0])
        self.assertFalse(check_phrase("go")[0])                   # too short
        self.assertFalse(check_phrase("hey wield")[0])            # wake phrase
        self.assertFalse(check_phrase("one two three four five six")[0])
        self.assertFalse(check_phrase("Next slide", ["next slide"])[0])

    def test_average_confidence(self):
        self.assertEqual(average_confidence({}), 1.0)
        self.assertAlmostEqual(
            average_confidence({"result": [{"conf": 0.9}, {"conf": 0.5}]}), 0.7
        )


class MatcherTests(unittest.TestCase):

    def setUp(self):
        self.clock = Clock()
        self.m = VoiceCommandMatcher(PHRASES, wake_word=True, wake_window=5, clock=self.clock)

    def test_wake_and_command_in_one_go(self):
        e = self.m.process("hey wield next slide")
        self.assertEqual((e.kind, e.trigger), ("command", "🎤 next slide"))

    def test_command_without_wake_word_is_ignored(self):
        e = self.m.process("next slide")
        self.assertEqual(e.kind, "ignored")
        self.assertIn("hey wield", e.reason)

    def test_wake_then_command_within_window(self):
        self.assertEqual(self.m.process("hey wield").kind, "armed")
        self.clock.t += 4
        self.assertEqual(self.m.process("go back").trigger, "🎤 go back")
        # One wake phrase, one command.
        self.assertEqual(self.m.process("go back").kind, "ignored")

    def test_wake_window_expires(self):
        self.m.process("hey wield")
        self.clock.t += 6
        self.assertEqual(self.m.process("next slide").kind, "ignored")

    def test_unknown_and_silence(self):
        self.assertIsNone(self.m.process(""))
        self.assertIsNone(self.m.process(UNKNOWN))
        self.assertEqual(self.m.process("hey wield [unk]").kind, "armed")
        self.assertEqual(self.m.process("hey wield open the pod bay doors").kind, "ignored")

    def test_low_confidence_is_ignored(self):
        e = self.m.process("hey wield next slide", confidence=0.3)
        self.assertEqual(e.kind, "ignored")

    def test_without_wake_word(self):
        m = VoiceCommandMatcher(PHRASES, wake_word=False)
        self.assertEqual(m.process("next slide").trigger, "🎤 next slide")
        self.assertEqual(m.process("Wield next slide").trigger, "🎤 next slide")


class ModelDownloadTests(unittest.TestCase):

    def fake_opener(self, payload):
        class Response(io.BytesIO):
            headers = {"Content-Length": str(len(payload))}

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        return lambda url: Response(payload)

    def model_zip(self, folder="vosk-model-small-en-us-0.15", valid=True):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr(f"{folder}/README", "model")
            if valid:
                z.writestr(f"{folder}/am/final.mdl", "x")
                z.writestr(f"{folder}/conf/model.conf", "x")
        return buf.getvalue()

    def test_download_installs_model(self):
        from backend.voice.model import download_model, model_ready
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, "voice", "vosk-model-small-en-us-0.15")
            seen = []
            download_model(
                progress=lambda d, t: seen.append((d, t)),
                target=target,
                opener=self.fake_opener(self.model_zip()),
            )
            self.assertTrue(model_ready(target))
            self.assertTrue(seen and seen[-1][0] == seen[-1][1])

    def test_bad_download_leaves_nothing_behind(self):
        from backend.voice.model import download_model
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, "voice", "m")
            with self.assertRaises(RuntimeError):
                download_model(target=target, opener=self.fake_opener(self.model_zip(valid=False)))
            self.assertFalse(os.path.exists(target))
            self.assertEqual(os.listdir(os.path.join(tmp, "voice")), [])


class FakeRecognizer:
    """Returns scripted Vosk results, one per audio chunk."""

    def __init__(self, results):
        self.results = list(results)
        self.current = None

    def AcceptWaveform(self, data):
        self.current = self.results.pop(0) if self.results else {"text": ""}
        return True

    def Result(self):
        return json.dumps(self.current)

    def FinalResult(self):
        return json.dumps({"text": ""})


class FakeStream:
    def __init__(self, callback, chunks):
        self.callback, self.chunks = callback, chunks
        self.closed = False

    def start(self):
        for _ in range(self.chunks):
            self.callback(b"\x00" * 10)

    def stop(self):
        pass

    def close(self):
        self.closed = True


@unittest.skipUnless(HAVE_QT, "PySide6 not installed")
class VoiceWorkerTests(unittest.TestCase):

    def run_worker(self, results, wake_word=True):
        from backend.voice.voice_worker import VoiceWorker

        streams = []

        def stream_factory(callback):
            streams.append(FakeStream(callback, len(results)))
            return streams[-1]

        worker = VoiceWorker(
            PHRASES,
            wake_word=wake_word,
            recognizer_factory=lambda phrases, wake: FakeRecognizer(results),
            stream_factory=stream_factory,
        )
        out = {"commands": [], "armed": 0, "errors": [], "heard": []}
        worker.command.connect(out["commands"].append)
        worker.armed.connect(lambda: out.__setitem__("armed", out["armed"] + 1))
        worker.error.connect(out["errors"].append)
        worker.heard.connect(lambda text, what: out["heard"].append((text, what)))

        # Stop once the scripted audio has been consumed.
        original = worker._handle

        def handle(result):
            original(result)
            if worker._audio.empty():
                worker.stop()

        worker._handle = handle
        worker.run()
        out["stream"] = streams[0] if streams else None
        return out

    def test_commands_and_wake(self):
        out = self.run_worker([
            {"text": "next slide"},                                    # no wake word
            {"text": "hey wield next slide", "result": [{"conf": 0.9}] * 3},
            {"text": "hey wield"},
            {"text": "go back"},
        ])
        self.assertEqual(out["commands"], ["🎤 next slide", "🎤 go back"])
        self.assertEqual(out["armed"], 1)
        self.assertEqual(out["errors"], [])
        self.assertTrue(out["stream"].closed)
        self.assertIn(("next slide", 'say "hey wield" first'), out["heard"])

    def test_microphone_failure_is_reported(self):
        from backend.voice.voice_worker import VoiceWorker

        class Broken:
            def start(self):
                raise OSError("no input device")

        worker = VoiceWorker(
            PHRASES,
            recognizer_factory=lambda p, w: FakeRecognizer([]),
            stream_factory=lambda cb: Broken(),
        )
        errors = []
        worker.error.connect(errors.append)
        worker.run()
        self.assertTrue(errors and "microphone" in errors[0])

    def test_missing_model_is_reported(self):
        from backend.voice import voice_worker as vw

        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.dict(os.environ, {"WIELD_DATA_DIR": tmp}):
            worker = vw.VoiceWorker(PHRASES)
            errors = []
            worker.error.connect(errors.append)
            worker.run()
        self.assertTrue(errors and "Settings" in errors[0])


class VoiceTriggerCatalogueTests(unittest.TestCase):

    def test_voice_group_and_kind(self):
        from backend.automation.triggers import VOICE, catalogue, trigger_kind
        groups = dict(catalogue([], [], ["🎤 next one please"]))
        self.assertIn("🎤 next slide", groups["Voice commands"])
        self.assertIn("🎤 next one please", groups["Voice commands"])
        self.assertEqual(trigger_kind("🎤 next slide"), VOICE)

    def test_default_presentation_profile_has_voice_triggers(self):
        from backend.paths import APP_DIR
        with open(os.path.join(APP_DIR, "backend", "config", "profiles", "presentation.json"),
                  encoding="utf-8") as f:
            gesture_map = json.load(f)["gesture_map"]
        self.assertEqual(gesture_map["🎤 next slide"], "presentation_next")


if __name__ == "__main__":
    unittest.main()


class DefaultVoicePhrasesTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        env = mock.patch.dict(os.environ, {"WIELD_DATA_DIR": self.tmp.name})
        env.start()
        self.addCleanup(env.stop)
        self.addCleanup(self.tmp.cleanup)

    def profile_without_voice(self):
        from backend.profile_manager import ProfileManager
        pm = ProfileManager()
        pm.load("presentation")
        for trigger in [t for t in pm.get_gesture_map() if is_voice_trigger(t)]:
            pm.remove_gesture(trigger)
        return pm

    def test_adds_standard_phrases_once(self):
        from backend.profile_manager import ProfileManager
        from backend.voice.defaults import add_default_voice_phrases

        pm = self.profile_without_voice()
        added = add_default_voice_phrases(pm)
        self.assertIn("next slide", added)

        fresh = ProfileManager()
        fresh.load("presentation")
        self.assertEqual(fresh.get_gesture_map()["🎤 next slide"], "presentation_next")

        # Removed by the user later: not added back.
        fresh.remove_gesture("🎤 next slide")
        self.assertEqual(add_default_voice_phrases(fresh), [])
        self.assertNotIn("🎤 next slide", fresh.get_gesture_map())

    def test_leaves_existing_voice_setup_alone(self):
        from backend.voice.defaults import add_default_voice_phrases

        pm = self.profile_without_voice()
        pm.update_gesture("🎤 onwards", "presentation_next")
        self.assertEqual(add_default_voice_phrases(pm), [])
        self.assertNotIn("🎤 next slide", pm.get_gesture_map())

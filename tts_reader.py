from kokoro_onnx import Kokoro
from kokoro_onnx.tokenizer import Tokenizer
from phonemizer.backend import EspeakBackend
from phonemizer.separator import default_separator
import sounddevice as sd
import threading
import hashlib
import numpy as np
import re
import html
import os
import wave
import requests
from collections import OrderedDict

_MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
_MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx"
_VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"

# ── espeak serialization (0xC0000005 crash fix) ───────────────────────────────
# kokoro's Tokenizer.phonemize calls the module-level phonemizer.phonemize(),
# which constructs a NEW EspeakBackend on EVERY call: each one copies
# espeak-ng.dll into a fresh temp dir, LoadLibrary's the copy, runs
# espeak_Initialize and registers an atexit FreeLibrary. Under this module's
# prefetch fan-out that happens on up to 8 threads at once -- and phonemizer
# documents espeak as thread-unsafe ("massive use of global variables"). The
# concurrent load/init corrupted the process heap and faulted in ntdll
# (0xC0000005) partway through the Phase 1 veto gate.
#
# Fix: reuse ONE backend per language, and serialize the phonemize call so
# espeak is never re-entered. ONNX inference is deliberately left OUTSIDE the
# lock -- it is ~96% of synthesis cost, is thread-safe, and keeping it parallel
# preserves the prefetcher's 2.86x speedup.
#
# The backend is built LAZILY, not at import: kokoro's Tokenizer.__init__ is
# what points phonemizer at the bundled espeak library, so a backend created at
# import time would resolve against the wrong library.
_PHONEME_LOCK = threading.Lock()
_ESPEAK_BACKENDS = {}


def _phonemize_serialized(self, text, lang="en-us", norm=True) -> str:
    """Drop-in replacement for kokoro_onnx.tokenizer.Tokenizer.phonemize.

    Mirrors the original's contract exactly -- normalize, phonemize, filter
    against the vocab, strip. The only behavioural changes are the shared
    backend and the lock.
    """
    if norm:
        text = Tokenizer.normalize_text(text)
    # phonemizer's _phonemize() strips os.linesep and yields "" for blank
    # input; reproduced here so the replacement matches on edge cases too.
    line = text.strip(os.linesep)
    if not line.strip():
        return ""
    with _PHONEME_LOCK:
        backend = _ESPEAK_BACKENDS.get(lang)
        if backend is None:
            backend = EspeakBackend(
                lang, preserve_punctuation=True, with_stress=True)
            _ESPEAK_BACKENDS[lang] = backend
        phonemes = backend.phonemize(
            [line], separator=default_separator, strip=False, njobs=1)[0]
    phonemes = "".join(filter(lambda p: p in self.vocab, phonemes))
    return phonemes.strip()


Tokenizer.phonemize = _phonemize_serialized


def _download_if_missing(url, path):
    if not os.path.exists(path):
        print(f" [TTS] Downloading {os.path.basename(path)}...")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        for attempt in range(3):
            try:
                r = requests.get(url, stream=True, timeout=120, allow_redirects=True)
                r.raise_for_status()
                with open(path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=65536):
                        f.write(chunk)
                print(f" [TTS] {os.path.basename(path)} ready.")
                return
            except Exception as e:
                if attempt == 2:
                    raise
                print(f" [TTS] Retry {attempt + 1}/3 ({e})")
                import time; time.sleep(2)


class Speaker:
    _CACHE_MAX = 20

    def __init__(self, voice="af_heart"):
        self.voice = voice
        self._kokoro = None
        self._thread = None
        self._play_id = 0
        self._cache = OrderedDict()  # key -> (threading.Event, clips_or_None)
        self._cache_lock = threading.Lock()

    def _ensure_loaded(self):
        if self._kokoro is None:
            model_path = os.path.join(_MODEL_DIR, "kokoro-v1.0.int8.onnx")
            voices_path = os.path.join(_MODEL_DIR, "voices-v1.0.bin")
            _download_if_missing(_MODEL_URL, model_path)
            _download_if_missing(_VOICES_URL, voices_path)
            self._kokoro = Kokoro(model_path, voices_path)

    def _split(self, text):
        parts = [p.strip() for p in re.split(r'(?<=[.!?])\s+', text) if p.strip()]
        return parts if parts else [text]

    def _synthesize(self, part):
        # Period trick: makes kokoro generate a sentence-ending pause buffer BEFORE trim runs.
        safe = part if part and part[-1] in '.!?,' else part + '.'
        samples, sample_rate = self._kokoro.create(safe, voice=self.voice, speed=1.0, lang="en-us")
        # Numpy pad: adds 300ms of silence AFTER trim has already run — the trim cannot
        # reach back and clip it, so the final phoneme is guaranteed to be fully audible.
        tail = np.zeros(int(0.3 * sample_rate), dtype=samples.dtype)
        return np.concatenate([samples, tail]), sample_rate

    def prefetch(self, text):
        if not text:
            return
        self._ensure_loaded()
        key = hashlib.md5(text.encode()).hexdigest()
        with self._cache_lock:
            if key in self._cache:
                return
            ready = threading.Event()
            self._cache[key] = (ready, None)

        def _generate():
            clips = []
            for part in self._split(text):
                try:
                    samples, sample_rate = self._synthesize(part)
                    clips.append((samples, sample_rate))
                except Exception:
                    with self._cache_lock:
                        entry = self._cache.get(key)
                        if entry and entry[0] is ready:
                            del self._cache[key]
                    ready.set()
                    return
            with self._cache_lock:
                entry = self._cache.get(key)
                if entry and entry[0] is ready:
                    self._cache[key] = (ready, clips)
                    self._cache.move_to_end(key)
                    while len(self._cache) > self._CACHE_MAX:
                        self._cache.popitem(last=False)
            ready.set()

        threading.Thread(target=_generate, daemon=True).start()

    def play(self, text):
        self._ensure_loaded()
        self._play_id += 1
        current_id = self._play_id
        key = hashlib.md5(text.encode()).hexdigest()

        def _run():
            with self._cache_lock:
                entry = self._cache.get(key)

            clips = None
            if entry is not None:
                ready, cached_clips = entry
                if cached_clips is None:
                    # Generation in progress — wait for it rather than streaming from scratch
                    ready.wait(timeout=10.0)
                with self._cache_lock:
                    entry = self._cache.get(key)
                    if entry is not None:
                        _, cached_clips = entry
                        if cached_clips is not None:
                            clips = cached_clips
                        del self._cache[key]

            if clips is not None:
                for samples, sample_rate in clips:
                    if self._play_id != current_id:
                        return
                    sd.play(samples, samplerate=sample_rate)
                    sd.wait()
            else:
                for part in self._split(text):
                    if self._play_id != current_id:
                        return
                    try:
                        samples, sample_rate = self._synthesize(part)
                    except Exception:
                        return
                    if self._play_id != current_id:
                        return
                    sd.play(samples, samplerate=sample_rate)
                    sd.wait()

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def stop(self):
        self._play_id += 1
        sd.stop()

    def render_to_file(self, text, media_dir, ext):
        """Synthesize `text` to one audio file in media_dir, named by content
        hash; idempotent (returns the existing filename without re-rendering if
        already present). `ext` is 'mp3' or 'wav', decided once per run by the
        caller's lameenc probe. Returns the bare filename for an Anki [sound:] tag."""
        key = hashlib.md5(text.encode()).hexdigest()
        filename = f"af_heart_{key}.{ext}"
        out_path = os.path.join(media_dir, filename)
        if os.path.exists(out_path):
            return filename
        self._ensure_loaded()
        clips = []
        sample_rate = 24000
        for part in self._split(text):
            samples, sample_rate = self._synthesize(part)
            clips.append(samples)
        buf = np.concatenate(clips) if clips else np.zeros(1, dtype=np.float32)
        # Kokoro returns float32 in ~[-1.0, 1.0]; wave/lameenc require int16 PCM.
        pcm = (np.clip(buf, -1.0, 1.0) * 32767.0).astype(np.int16)
        if ext == "mp3":
            import lameenc
            encoder = lameenc.Encoder()
            encoder.set_bit_rate(48)
            encoder.set_in_sample_rate(sample_rate)
            encoder.set_channels(1)
            encoder.set_quality(2)
            data = encoder.encode(pcm.tobytes())
            data += encoder.flush()
            with open(out_path, "wb") as fh:
                fh.write(data)
        else:
            with wave.open(out_path, "wb") as wv:
                wv.setnchannels(1)
                wv.setsampwidth(2)
                wv.setframerate(sample_rate)
                wv.writeframes(pcm.tobytes())
        return filename


def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r'\[USER\]|\[INJECTED\]|\[T\d+\]', '', text)
    text = re.sub(r'(?m)^📊 Matrix:.*', '', text)
    text = re.sub(r'(?m)^Attribute: auto_added.*', '', text)
    text = re.sub(r'<br\s*/?>', ', ', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    text = text.replace('**', '')
    text = ' '.join(text.split())
    return text.strip()


def build_speech_p1(label, trigger_txt=""):
    label_clean = clean_text(label)
    trigger_clean = clean_text(trigger_txt)
    if trigger_clean:
        return label_clean + ". Trigger: " + trigger_clean
    return label_clean


def build_speech_p2(goal_label, concept, preview, reasoning=""):
    goal_clean = clean_text(goal_label)
    concept_clean = clean_text(concept)
    preview_clean = clean_text(preview)
    reasoning_clean = clean_text(reasoning)
    parts = [goal_clean, concept_clean, preview_clean]
    if reasoning_clean:
        parts.append(reasoning_clean)
    return ". ".join(p for p in parts if p)


def build_speech_p5(front_text, back_text=""):
    front_clean = clean_text(front_text)
    back_clean = clean_text(back_text)
    if back_clean:
        return front_clean + ". Answer: " + back_clean
    return front_clean


speaker = Speaker()

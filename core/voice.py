"""
voice.py — offline speech-to-text and text-to-speech for Alfred.

Keeps the same privacy contract as the rest of the app:
  - STT: faster-whisper, a local CTranslate2 re-implementation of Whisper.
    The model weights download once (from Hugging Face) on first use and are
    cached under ~/.cache/huggingface; every call after that is fully offline.
  - TTS: pyttsx3, which drives the operating system's own built-in speech
    engine (SAPI5 on Windows, NSSpeechSynthesizer on macOS, espeak/espeak-ng
    on Linux). No network call is ever made for TTS.

Both are lazy-loaded: the (comparatively heavy) Whisper model is only loaded
into memory the first time transcribe() is actually called, not at import
time, so app startup stays fast if voice is never used.
"""

import io
import tempfile
import wave
from pathlib import Path

from config import STT_MODEL_SIZE, STT_DEVICE, STT_COMPUTE_TYPE, TTS_RATE, TTS_VOLUME


class SpeechToText:
    """Lazy-loaded local Whisper model via faster-whisper."""

    def __init__(self, model_size: str = STT_MODEL_SIZE):
        self.model_size = model_size
        self._model = None

    def _ensure_loaded(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            # First call downloads+caches the model; every call after is offline.
            self._model = WhisperModel(
                self.model_size, device=STT_DEVICE, compute_type=STT_COMPUTE_TYPE
            )

    def transcribe(self, audio_bytes: bytes, suffix: str = ".webm") -> str:
        """Transcribe raw audio bytes (whatever the browser recorded: webm/ogg/wav)
        into text. Writes to a temp file since faster-whisper/ffmpeg expects a path."""
        self._ensure_loaded()
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
            tmp.write(audio_bytes)
            tmp.flush()
            segments, _info = self._model.transcribe(tmp.name, beam_size=5)
            return "".join(seg.text for seg in segments).strip()


class TextToSpeech:
    """Local, offline TTS using the OS's own speech engine via pyttsx3."""

    def __init__(self, rate: int = TTS_RATE, volume: float = TTS_VOLUME):
        self.rate = rate
        self.volume = volume

    def speak_to_wav(self, text: str) -> bytes:
        """Render text to WAV audio bytes (does not play out loud on the server;
        the caller/browser is responsible for playback). Returns raw WAV bytes."""
        import pyttsx3

        # pyttsx3 can only write to a real file path (not an in-memory buffer),
        # so we render to a temp file and read the bytes back.
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", self.rate)
            engine.setProperty("volume", self.volume)
            engine.save_to_file(text, tmp_path)
            engine.runAndWait()
            return Path(tmp_path).read_bytes()
        finally:
            Path(tmp_path).unlink(missing_ok=True)


# Module-level singletons, lazily initialized — mirrors how embeddings.py
# and other heavy-model wrappers are used elsewhere in the app.
stt = SpeechToText()
tts = TextToSpeech()

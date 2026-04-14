"""
Speech transcription using OpenAI Whisper (local inference).

The model is loaded lazily on first use and cached for subsequent calls.
"""

from __future__ import annotations

import contextlib
import io
import threading
from typing import Optional

import numpy as np

try:
    import whisper  # openai-whisper
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "openai-whisper is required: pip install openai-whisper"
    ) from exc


class Transcriber:
    """Wraps an OpenAI Whisper model and transcribes float32 audio arrays."""

    def __init__(self, model_name: str = "base") -> None:
        self._model_name = model_name
        self._model = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Pre-load the Whisper model (blocking).  Call once at startup."""
        with self._lock:
            if self._model is None:
                self._model = self._load_model()

    def transcribe(
        self,
        audio: np.ndarray,
        language: Optional[str] = None,
    ) -> str:
        """
        Transcribe *audio* (float32, 16 kHz, mono) and return the text.

        Parameters
        ----------
        audio:
            Raw float32 samples at 16 000 Hz.
        language:
            ISO-639-1 code ('de', 'pl', 'en') or None for auto-detect.
        """
        with self._lock:
            if self._model is None:
                self._model = self._load_model()

        if audio is None or len(audio) == 0:
            return ""

        result = self._model.transcribe(
            audio,
            language=language,
            fp16=False,
        )
        return result.get("text", "").strip()

    def transcribe_chunk(
        self,
        audio: np.ndarray,
        language: Optional[str] = None,
    ) -> str:
        """Transcribe a live audio chunk using the same model instance."""
        return self.transcribe(audio, language=language)

    def set_model(self, model_name: str) -> None:
        """Switch model (invalidates any cached model)."""
        with self._lock:
            self._model_name = model_name
            self._model = None

    def _load_model(self):
        """Load a Whisper model without tqdm writing to a missing thread console."""
        sink = io.StringIO()
        with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            return whisper.load_model(self._model_name)

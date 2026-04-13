"""
Audio recorder – captures microphone input into a NumPy float32 array.
Recording runs on a background thread; the result is retrieved via
``stop()`` which blocks until the thread finishes.
"""

from __future__ import annotations

import threading
from typing import Optional

import numpy as np

try:
    import sounddevice as sd
except ImportError as exc:  # pragma: no cover
    raise ImportError("sounddevice is required: pip install sounddevice") from exc

SAMPLE_RATE = 16_000   # Hz – Whisper expects 16 kHz
CHANNELS = 1


class Recorder:
    """Manages a single recording session."""

    def __init__(self, device_index: Optional[int] = None) -> None:
        self._device_index = device_index
        self._frames: list[np.ndarray] = []
        self._stream: Optional[sd.InputStream] = None
        self._recording = threading.Event()
        self._thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Begin capturing audio in a background thread."""
        if self._recording.is_set():
            return
        self._frames = []
        self._recording.set()
        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()

    def stop(self) -> np.ndarray:
        """Stop capturing and return the recorded audio as float32 array."""
        self._recording.clear()
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None
        if not self._frames:
            return np.zeros(0, dtype=np.float32)
        audio = np.concatenate(self._frames, axis=0).flatten()
        return audio.astype(np.float32)

    @property
    def is_recording(self) -> bool:
        return self._recording.is_set()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _record_loop(self) -> None:
        def callback(indata: np.ndarray, frames: int, time, status) -> None:  # noqa: ARG001
            if self._recording.is_set():
                self._frames.append(indata.copy())

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            device=self._device_index,
            callback=callback,
        ):
            while self._recording.is_set():
                sd.sleep(100)


def list_microphones() -> list[dict]:
    """Return a list of available input devices with 'index' and 'name'."""
    devices = []
    for idx, dev in enumerate(sd.query_devices()):
        if dev["max_input_channels"] > 0:
            devices.append({"index": idx, "name": dev["name"]})
    return devices

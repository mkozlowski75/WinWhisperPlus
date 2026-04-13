"""
Settings management for MyWhisper.
Persists configuration to a JSON file in the user's AppData directory.
"""

import json
import os
from pathlib import Path

DEFAULT_SETTINGS = {
    "hotkey_record": "alt+shift+r",
    "hotkey_language": "alt+shift+s",
    "language": "de",           # 'de', 'pl', 'en'
    "microphone_index": None,   # None = system default
    "whisper_model": "base",    # tiny, base, small, medium, large
    "auto_insert": True,
}

LANGUAGES = {
    "de": "Deutsch",
    "pl": "Polski",
    "en": "English",
}

LANGUAGE_CYCLE = ["de", "pl", "en"]


def _config_path() -> Path:
    """Return path to the JSON settings file."""
    app_data = os.environ.get("APPDATA") or Path.home()
    config_dir = Path(app_data) / "MyWhisper"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "settings.json"


class Settings:
    """Loads, holds and persists application settings."""

    def __init__(self) -> None:
        self._path = _config_path()
        self._data: dict = dict(DEFAULT_SETTINGS)
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as fh:
                    stored = json.load(fh)
                # Merge with defaults so new keys are always present
                self._data.update({k: v for k, v in stored.items() if k in DEFAULT_SETTINGS})
            except (json.JSONDecodeError, OSError):
                pass  # fall back to defaults

    def save(self) -> None:
        try:
            with open(self._path, "w", encoding="utf-8") as fh:
                json.dump(self._data, fh, indent=2, ensure_ascii=False)
        except OSError:
            pass

    # ------------------------------------------------------------------
    # Property accessors
    # ------------------------------------------------------------------

    @property
    def hotkey_record(self) -> str:
        return self._data["hotkey_record"]

    @hotkey_record.setter
    def hotkey_record(self, value: str) -> None:
        self._data["hotkey_record"] = value

    @property
    def hotkey_language(self) -> str:
        return self._data["hotkey_language"]

    @hotkey_language.setter
    def hotkey_language(self, value: str) -> None:
        self._data["hotkey_language"] = value

    @property
    def language(self) -> str:
        return self._data["language"]

    @language.setter
    def language(self, value: str) -> None:
        if value in LANGUAGE_CYCLE:
            self._data["language"] = value

    @property
    def microphone_index(self):
        return self._data["microphone_index"]

    @microphone_index.setter
    def microphone_index(self, value) -> None:
        self._data["microphone_index"] = value

    @property
    def whisper_model(self) -> str:
        return self._data["whisper_model"]

    @whisper_model.setter
    def whisper_model(self, value: str) -> None:
        self._data["whisper_model"] = value

    @property
    def auto_insert(self) -> bool:
        return self._data["auto_insert"]

    @auto_insert.setter
    def auto_insert(self, value: bool) -> None:
        self._data["auto_insert"] = bool(value)

    def cycle_language(self) -> str:
        """Switch to the next language in the cycle and return its code."""
        idx = LANGUAGE_CYCLE.index(self.language)
        self.language = LANGUAGE_CYCLE[(idx + 1) % len(LANGUAGE_CYCLE)]
        return self.language

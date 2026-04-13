"""Tests for config/settings.py"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Patch the config path to use a temp directory for all tests
@pytest.fixture(autouse=True)
def temp_config(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    yield tmp_path


def _make_settings():
    from config.settings import Settings
    return Settings()


def test_default_settings():
    s = _make_settings()
    assert s.hotkey_record == "alt+shift+r"
    assert s.hotkey_language == "alt+shift+s"
    assert s.language == "de"
    assert s.microphone_index is None
    assert s.whisper_model == "base"
    assert s.auto_insert is True


def test_save_and_reload(tmp_path):
    s = _make_settings()
    s.language = "pl"
    s.hotkey_record = "ctrl+shift+r"
    s.save()

    s2 = _make_settings()
    assert s2.language == "pl"
    assert s2.hotkey_record == "ctrl+shift+r"


def test_cycle_language():
    s = _make_settings()
    assert s.language == "de"
    lang = s.cycle_language()
    assert lang == "pl"
    lang = s.cycle_language()
    assert lang == "en"
    lang = s.cycle_language()
    assert lang == "de"


def test_invalid_language_ignored():
    s = _make_settings()
    s.language = "xx"
    assert s.language == "de"  # unchanged


def test_corrupted_json_falls_back_to_defaults(tmp_path):
    config_dir = tmp_path / "MyWhisper"
    config_dir.mkdir()
    (config_dir / "settings.json").write_text("not-valid-json")
    s = _make_settings()
    assert s.hotkey_record == "alt+shift+r"


def test_partial_json_merges_with_defaults(tmp_path):
    config_dir = tmp_path / "MyWhisper"
    config_dir.mkdir()
    (config_dir / "settings.json").write_text(json.dumps({"language": "en"}))
    s = _make_settings()
    assert s.language == "en"
    assert s.hotkey_record == "alt+shift+r"  # default preserved

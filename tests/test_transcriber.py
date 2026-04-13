"""Tests for core/transcriber.py (mocking openai-whisper)"""

import sys
import numpy as np
import pytest
from unittest.mock import MagicMock


@pytest.fixture(autouse=True)
def mock_whisper(monkeypatch):
    """Replace openai-whisper with a mock that returns predictable text."""
    whisper_mock = MagicMock()
    model_mock = MagicMock()
    model_mock.transcribe.return_value = {"text": "  Hallo Welt  "}
    whisper_mock.load_model.return_value = model_mock
    monkeypatch.setitem(sys.modules, "whisper", whisper_mock)
    # Force re-import so the module picks up the new whisper mock
    monkeypatch.delitem(sys.modules, "core.transcriber", raising=False)
    yield whisper_mock, model_mock


def test_transcribe_returns_stripped_text(mock_whisper):
    from core.transcriber import Transcriber
    _, model_mock = mock_whisper
    t = Transcriber(model_name="base")
    audio = np.zeros(16000, dtype=np.float32)
    result = t.transcribe(audio, language="de")
    assert result == "Hallo Welt"
    model_mock.transcribe.assert_called_once()


def test_transcribe_empty_audio(mock_whisper):
    from core.transcriber import Transcriber
    t = Transcriber()
    result = t.transcribe(np.zeros(0, dtype=np.float32), language="de")
    assert result == ""


def test_transcribe_none_audio(mock_whisper):
    from core.transcriber import Transcriber
    t = Transcriber()
    result = t.transcribe(None, language="de")
    assert result == ""


def test_set_model_invalidates_cache(mock_whisper):
    whisper_mock, _ = mock_whisper
    from core.transcriber import Transcriber
    t = Transcriber(model_name="base")
    audio = np.zeros(16000, dtype=np.float32)
    t.transcribe(audio)
    assert whisper_mock.load_model.call_count == 1

    t.set_model("small")
    t.transcribe(audio)
    assert whisper_mock.load_model.call_count == 2


def test_load_preloads_model(mock_whisper):
    whisper_mock, _ = mock_whisper
    from core.transcriber import Transcriber
    t = Transcriber(model_name="tiny")
    t.load()
    assert whisper_mock.load_model.call_count == 1
    # subsequent transcribe should not reload
    audio = np.zeros(16000, dtype=np.float32)
    t.transcribe(audio)
    assert whisper_mock.load_model.call_count == 1

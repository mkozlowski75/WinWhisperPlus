"""Tests for core/hotkey_manager.py (mocking keyboard library)"""

import sys
import pytest
from unittest.mock import MagicMock


@pytest.fixture(autouse=True)
def mock_keyboard(monkeypatch):
    kb_mock = MagicMock()
    kb_mock.add_hotkey.side_effect = lambda hk, cb, **kw: hash(hk)
    monkeypatch.setitem(sys.modules, "keyboard", kb_mock)
    # Ensure the module is re-imported fresh so it picks up the new mock
    monkeypatch.delitem(sys.modules, "core.hotkey_manager", raising=False)
    yield kb_mock


def test_register_hotkey(mock_keyboard):
    from core.hotkey_manager import HotkeyManager
    mgr = HotkeyManager()
    cb = MagicMock()
    mgr.register("alt+shift+r", cb)
    mock_keyboard.add_hotkey.assert_called_once_with(
        "alt+shift+r", cb, suppress=False
    )


def test_register_replaces_existing(mock_keyboard):
    from core.hotkey_manager import HotkeyManager
    mgr = HotkeyManager()
    cb1, cb2 = MagicMock(), MagicMock()
    mgr.register("alt+shift+r", cb1)
    mgr.register("alt+shift+r", cb2)
    # Should unregister old one and register new one
    assert mock_keyboard.remove_hotkey.call_count == 1
    assert mock_keyboard.add_hotkey.call_count == 2


def test_unregister_hotkey(mock_keyboard):
    from core.hotkey_manager import HotkeyManager
    mgr = HotkeyManager()
    mgr.register("alt+shift+r", MagicMock())
    mgr.unregister("alt+shift+r")
    assert mock_keyboard.remove_hotkey.call_count == 1
    assert "alt+shift+r" not in mgr._hooks


def test_unregister_unknown_hotkey(mock_keyboard):
    """Unregistering a hotkey that was never registered should not raise."""
    from core.hotkey_manager import HotkeyManager
    mgr = HotkeyManager()
    mgr.unregister("ctrl+x")  # should be silent


def test_unregister_all(mock_keyboard):
    from core.hotkey_manager import HotkeyManager
    mgr = HotkeyManager()
    mgr.register("alt+shift+r", MagicMock())
    mgr.register("alt+shift+s", MagicMock())
    mgr.unregister_all()
    assert len(mgr._hooks) == 0
    assert mock_keyboard.remove_hotkey.call_count == 2

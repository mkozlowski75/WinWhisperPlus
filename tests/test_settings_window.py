from __future__ import annotations

import pytest

from PyQt6.QtWidgets import QApplication

from config.settings import Settings
from gui.settings_window import SettingsWindow


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_settings_window_shows_version(qapp, monkeypatch):
    monkeypatch.setattr("gui.settings_window.list_microphones", lambda: [])
    monkeypatch.setattr("gui.settings_window.app_version", lambda: "9.8.7")

    window = SettingsWindow(Settings())

    assert window._version_label.text() == "Version: 9.8.7"

    window.close()

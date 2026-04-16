"""
MyWhisper – Entry point.

Usage:
    python main.py
"""

from __future__ import annotations

import sys

# Only import lightweight modules here so the window can appear before
# the heavy modules (whisper, sounddevice, keyboard) are loaded.
from PyQt6.QtWidgets import QApplication

from config.localization import tr
from config.settings import Settings
from gui.status_window import StatusWindow


def main() -> None:
    qapp = QApplication(sys.argv)
    qapp.setQuitOnLastWindowClosed(False)  # keep running when windows are closed
    qapp.setApplicationName("MyWhisper")
    qapp.setOrganizationName("MyWhisper")

    # Show the status window immediately with a loading indicator.
    # This makes the window appear (~200ms) before the heavy imports below.
    settings = Settings()
    status_window = StatusWindow(hotkey_record=settings.hotkey_record, settings=settings)
    status_window.load_position()
    status_window.set_loading(True, tr("initializing", settings))
    status_window.show()
    qapp.processEvents()  # Force Qt to paint the window NOW

    # Heavy imports happen here (whisper, sounddevice, keyboard ~2-3s).
    # The user already sees the window and loading spinner.
    from app import Application  # noqa: PLC0415

    application = Application(qapp, status_window=status_window, settings=settings)
    application.start()

    sys.exit(qapp.exec())


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()

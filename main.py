"""
MyWhisper – Entry point.

Usage:
    python main.py
"""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from app import Application


def main() -> None:
    qapp = QApplication(sys.argv)
    qapp.setQuitOnLastWindowClosed(False)  # keep running when windows are closed
    qapp.setApplicationName("MyWhisper")
    qapp.setOrganizationName("MyWhisper")

    application = Application(qapp)
    application.start()

    sys.exit(qapp.exec())


if __name__ == "__main__":
    main()

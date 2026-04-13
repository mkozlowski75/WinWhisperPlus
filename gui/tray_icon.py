"""
System tray icon for MyWhisper.

The tray icon provides quick access to:
 - Start/stop recording
 - Open settings
 - Quit the application
It also shows the current status via tooltip and optional icon badge.
"""

from __future__ import annotations

from typing import Callable

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter, QFont
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon, QApplication


def _make_icon(color: str, label: str = "") -> QIcon:
    """Generate a simple colored circle icon with an optional letter."""
    size = 32
    pix = QPixmap(size, size)
    pix.fill(QColor("transparent"))
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(color))
    painter.setPen(QColor("white"))
    painter.drawEllipse(2, 2, size - 4, size - 4)
    if label:
        font = QFont("Arial", 14, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(pix.rect(), 0x0084, label)  # AlignCenter
    painter.end()
    return QIcon(pix)


# Status colours
_ICONS = {
    "ready":       _make_icon("#4CAF50", "M"),   # green
    "recording":   _make_icon("#F44336", "●"),   # red
    "processing":  _make_icon("#FF9800", "…"),   # orange
    "inserted":    _make_icon("#2196F3", "✓"),   # blue
}

_STATUS_LABELS = {
    "ready":      "Bereit",
    "recording":  "Aufnahme läuft",
    "processing": "Verarbeitung läuft",
    "inserted":   "Text eingefügt",
}


class TrayIcon(QObject):
    """Wraps QSystemTrayIcon with application-specific behaviour."""

    toggle_recording_requested = pyqtSignal()
    open_settings_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._tray = QSystemTrayIcon(parent=None)
        self._tray.setIcon(_ICONS["ready"])
        self._tray.setToolTip("MyWhisper – Bereit")
        self._build_menu()
        self._tray.activated.connect(self._on_activated)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show(self) -> None:
        self._tray.show()

    def hide(self) -> None:
        self._tray.hide()

    def set_status(self, status: str) -> None:
        """Update icon and tooltip to reflect *status*."""
        icon = _ICONS.get(status, _ICONS["ready"])
        label = _STATUS_LABELS.get(status, status)
        self._tray.setIcon(icon)
        self._tray.setToolTip(f"MyWhisper – {label}")
        self._record_action.setText(
            "Aufnahme stoppen" if status == "recording" else "Aufnahme starten"
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_menu(self) -> None:
        menu = QMenu()

        self._record_action = menu.addAction("Aufnahme starten")
        self._record_action.triggered.connect(self.toggle_recording_requested)

        menu.addSeparator()

        settings_action = menu.addAction("Einstellungen…")
        settings_action.triggered.connect(self.open_settings_requested)

        menu.addSeparator()

        quit_action = menu.addAction("Beenden")
        quit_action.triggered.connect(self.quit_requested)

        self._tray.setContextMenu(menu)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.toggle_recording_requested.emit()

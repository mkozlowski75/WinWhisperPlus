"""
Small always-visible status window that shows the current application state.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QLabel, QWidget, QVBoxLayout

_STATUS_TEXTS = {
    "ready":      "Bereit",
    "recording":  "🔴 Aufnahme läuft",
    "processing": "⏳ Verarbeitung läuft",
    "inserted":   "✅ Text eingefügt",
}

_STATUS_COLORS = {
    "ready":      "#4CAF50",
    "recording":  "#F44336",
    "processing": "#FF9800",
    "inserted":   "#2196F3",
}


class StatusWindow(QWidget):
    """Compact floating status widget."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MyWhisper")
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setFixedSize(240, 60)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(8, 4, 8, 4)

        self._label = QLabel("Bereit")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self._layout.addWidget(self._label)

        self._msg_timer = QTimer(self)
        self._msg_timer.setSingleShot(True)
        self._msg_timer.timeout.connect(self._clear_message)
        self._base_status = "ready"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_status(self, status: str) -> None:
        self._base_status = status
        if not self._msg_timer.isActive():
            self._apply_status(status)

    def show_message(self, message: str, duration_ms: int = 2500) -> None:
        """Show a temporary overlay message for *duration_ms* milliseconds."""
        self._label.setText(message)
        self._label.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #9C27B0;"
        )
        self._msg_timer.start(duration_ms)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _apply_status(self, status: str) -> None:
        text = _STATUS_TEXTS.get(status, status)
        color = _STATUS_COLORS.get(status, "#000000")
        self._label.setText(text)
        self._label.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {color};"
        )

    def _clear_message(self) -> None:
        self._apply_status(self._base_status)

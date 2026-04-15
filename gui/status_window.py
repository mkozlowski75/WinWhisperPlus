"""
Small always-visible status window that shows the current application state.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QMoveEvent, QContextMenuEvent, QIcon, QPixmap, QColor, QPainter, QFont
from PyQt6.QtWidgets import QLabel, QWidget, QVBoxLayout, QMenu, QProgressBar

_STATUS_TEXTS = {
    "initializing": "Initialisierung",
    "ready":      "Bereit",
    "recording":  "🔴 Aufnahme läuft",
    "processing": "⏳ Verarbeitung läuft",
    "inserted":   "✅ Text eingefügt",
}

_STATUS_COLORS = {
    "initializing": "#FF9800",
    "ready":      "#4CAF50",
    "recording":  "#F44336",
    "processing": "#FF9800",
    "inserted":   "#2196F3",
}


def _format_hotkey(hotkey: str) -> str:
    """Convert hotkey format from 'alt+shift+r' to 'Alt+Shift+R'."""
    parts = hotkey.split("+")
    formatted = [part.capitalize() for part in parts]
    return "+".join(formatted)


class StatusWindow(QWidget):
    """Compact floating status widget."""

    toggle_recording_requested = pyqtSignal()
    open_settings_requested = pyqtSignal()
    open_history_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self, hotkey_record: str = "", settings=None) -> None:
        super().__init__()
        self._settings = settings
        self.setWindowTitle("MyWhisper")
        self.setWindowIcon(self._make_app_icon())
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setFixedWidth(200)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(8, 6, 8, 6)
        self._layout.setSpacing(4)

        self._label = QLabel("Initialisierung")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self._layout.addWidget(self._label)

        # Second row (normal state): hotkey information.
        self._hotkey_label = QLabel()
        self._hotkey_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hotkey_label.setStyleSheet("font-size: 11px; color: #666;")
        self._layout.addWidget(self._hotkey_label)

        # Second row (loading state): progress indicator.
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setFixedHeight(10)
        self._progress_bar.hide()
        self._layout.addWidget(self._progress_bar)

        self._msg_timer = QTimer(self)
        self._msg_timer.setSingleShot(True)
        self._msg_timer.timeout.connect(self._clear_message)
        self._base_status = "initializing"
        self._loading_active = False
        self._loading_message = "Modelle laden..."
        self._hotkey_record = _format_hotkey(hotkey_record) if hotkey_record else ""
        self._record_action = None  # Will be created when context menu is first built
        self._refresh_primary_line()
        self._update_hotkey_display()
        self._update_second_line_visibility()
        self._recompute_height()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_status(self, status: str) -> None:
        self._base_status = status
        if not self._msg_timer.isActive() and not self._loading_active:
            self._refresh_primary_line()
        # Update context menu recording action text
        if self._record_action:
            self._record_action.setText(
                "Aufnahme stoppen" if status == "recording" else "Aufnahme starten"
            )

    def set_hotkey(self, hotkey_record: str) -> None:
        """Update the displayed hotkey."""
        self._hotkey_record = _format_hotkey(hotkey_record) if hotkey_record else ""
        self._update_hotkey_display()

    def load_position(self) -> None:
        """Load and restore the window position from settings."""
        if self._settings and self._settings.window_position_x is not None and self._settings.window_position_y is not None:
            self.move(self._settings.window_position_x, self._settings.window_position_y)

    def show_message(self, message: str, duration_ms: int = 2500) -> None:
        """Show a temporary overlay message for *duration_ms* milliseconds."""
        self._label.setText(message)
        self._label.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #9C27B0;"
        )
        self._msg_timer.start(duration_ms)

    def set_loading(self, active: bool, message: str = "Modelle laden...") -> None:
        """Show or hide loading mode with progress in line 2."""
        self._loading_active = active
        self._loading_message = message
        self._update_second_line_visibility()
        if not self._msg_timer.isActive():
            self._refresh_primary_line()
        self._recompute_height()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _update_hotkey_display(self) -> None:
        """Update the hotkey display label."""
        if self._hotkey_record:
            self._hotkey_label.setText(f"Hotkey: {self._hotkey_record}")
        else:
            self._hotkey_label.setText("")

    def _update_second_line_visibility(self) -> None:
        """Only one element may be visible in the second line."""
        loading = self._loading_active
        self._hotkey_label.setVisible(not loading)
        self._progress_bar.setVisible(loading)
        if loading:
            self._progress_bar.setRange(0, 0)
            self._progress_bar.setTextVisible(False)

    def _refresh_primary_line(self) -> None:
        """Apply current line 1 text based on message/loading/status priority."""
        if self._loading_active:
            self._label.setText(self._loading_message)
            self._label.setStyleSheet("font-size: 12px; font-weight: bold; color: #444;")
            return
        self._apply_status(self._base_status)

    def _recompute_height(self) -> None:
        """Compute a compact height from active widgets (DPI-friendly)."""
        margins = self._layout.contentsMargins()
        spacing = max(self._layout.spacing(), 0)
        top_height = self._label.sizeHint().height()
        lower_widget = self._progress_bar if self._loading_active else self._hotkey_label
        lower_height = lower_widget.sizeHint().height()
        compact_height = margins.top() + top_height + spacing + lower_height + margins.bottom() + 8
        self.setFixedHeight(max(56, compact_height))

    def _apply_status(self, status: str) -> None:
        text = _STATUS_TEXTS.get(status, status)
        color = _STATUS_COLORS.get(status, "#000000")
        self._label.setText(text)
        self._label.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {color};"
        )

    def _clear_message(self) -> None:
        self._refresh_primary_line()

    def _make_app_icon(self) -> QIcon:
        """Load microphone SVG icon for the application window."""
        from pathlib import Path
        asset_path = Path(__file__).parent.parent / "assets" / "icon.svg"
        return QIcon(str(asset_path))

    def moveEvent(self, event: QMoveEvent) -> None:
        """Save window position when it moves."""
        super().moveEvent(event)
        if self._settings:
            self._settings.window_position_x = self.x()
            self._settings.window_position_y = self.y()
            self._settings.save()

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        """Display context menu on right-click."""
        menu = self._build_context_menu()
        menu.exec(event.globalPos())

    def _build_context_menu(self) -> QMenu:
        """Build context menu with same options as TrayIcon."""
        menu = QMenu(self)
        
        # Recording action
        self._record_action = menu.addAction("Aufnahme starten")
        self._record_action.triggered.connect(self.toggle_recording_requested.emit)
        
        # Separator
        menu.addSeparator()
        
        # History action
        history_action = menu.addAction("Verlauf…")
        history_action.triggered.connect(self.open_history_requested.emit)
        
        # Settings action
        settings_action = menu.addAction("Einstellungen…")
        settings_action.triggered.connect(self.open_settings_requested.emit)
        
        # Separator
        menu.addSeparator()
        
        # Quit action
        quit_action = menu.addAction("Beenden")
        quit_action.triggered.connect(self.quit_requested.emit)
        
        return menu

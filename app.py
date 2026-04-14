"""
Main application orchestrator.

Wires together:
  - Settings
  - Recorder
  - Transcriber
  - TextInserter
  - HotkeyManager
  - TrayIcon
  - SettingsWindow / StatusWindow
"""

from __future__ import annotations

import threading

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QApplication

from config.settings import LANGUAGES, Settings
from core.hotkey_manager import HotkeyManager
from core.recorder import Recorder
from core.transcriber import Transcriber
from core.text_inserter import insert_text
from gui.settings_window import SettingsWindow
from gui.tray_icon import TrayIcon
from gui.status_window import StatusWindow


class Application(QObject):
    """Top-level application controller."""

    # Signals are used to safely update the Qt GUI from background threads
    _status_changed = pyqtSignal(str)
    _transcription_done = pyqtSignal(str)

    def __init__(self, qapp: QApplication) -> None:
        super().__init__()
        self._qapp = qapp
        self._settings = Settings()
        self._recorder = Recorder(device_index=self._settings.microphone_index)
        self._transcriber = Transcriber(model_name=self._settings.whisper_model)
        self._hotkey_mgr = HotkeyManager()

        # GUI
        self._tray = TrayIcon(parent=self)
        self._status_window = StatusWindow(hotkey_record=self._settings.hotkey_record)

        self._connect_signals()
        self._apply_settings(self._settings)

        # Pre-load Whisper model in background so first use is fast
        threading.Thread(target=self._transcriber.load, daemon=True).start()

    # ------------------------------------------------------------------
    # Setup / teardown
    # ------------------------------------------------------------------

    def start(self) -> None:
        self._tray.show()
        self._status_window.set_status("ready")
        self._status_window.show()

    def shutdown(self) -> None:
        self._hotkey_mgr.unregister_all()
        if self._recorder.is_recording:
            self._recorder.stop()

    # ------------------------------------------------------------------
    # Signal wiring
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        self._tray.toggle_recording_requested.connect(self._toggle_recording)
        self._tray.open_settings_requested.connect(self._open_settings)
        self._tray.quit_requested.connect(self._quit)

        self._status_changed.connect(self._on_status_changed)
        self._transcription_done.connect(self._on_transcription_done)

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def _apply_settings(self, settings: Settings) -> None:
        """Register hotkeys and update recorder/transcriber from settings."""
        self._hotkey_mgr.unregister_all()
        self._hotkey_mgr.register(settings.hotkey_record, self._toggle_recording)
        self._hotkey_mgr.register(settings.hotkey_language, self._cycle_language)
        self._recorder = Recorder(device_index=settings.microphone_index)
        self._transcriber.set_model(settings.whisper_model)
        # Update the displayed hotkey in the status window
        self._status_window.set_hotkey(settings.hotkey_record)

    def _open_settings(self) -> None:
        dlg = SettingsWindow(self._settings)
        dlg.settings_saved.connect(self._apply_settings)
        dlg.exec()

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    @pyqtSlot()
    def _toggle_recording(self) -> None:
        if self._recorder.is_recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self) -> None:
        self._recorder.start()
        self._status_changed.emit("recording")

    def _stop_recording(self) -> None:
        audio = self._recorder.stop()
        self._status_changed.emit("processing")
        language = self._settings.language
        # Run transcription in a daemon thread to keep the UI responsive
        threading.Thread(
            target=self._transcribe_and_emit,
            args=(audio, language),
            daemon=True,
        ).start()

    def _transcribe_and_emit(self, audio, language: str) -> None:
        text = self._transcriber.transcribe(audio, language=language)
        self._transcription_done.emit(text)

    # ------------------------------------------------------------------
    # Language cycling
    # ------------------------------------------------------------------

    @pyqtSlot()
    def _cycle_language(self) -> None:
        lang = self._settings.cycle_language()
        self._settings.save()
        lang_name = LANGUAGES.get(lang, lang)
        self._status_window.show_message(f"Sprache: {lang_name}")

    # ------------------------------------------------------------------
    # Slots (always run on the Qt main thread via signal)
    # ------------------------------------------------------------------

    @pyqtSlot(str)
    def _on_status_changed(self, status: str) -> None:
        self._tray.set_status(status)
        self._status_window.set_status(status)

    @pyqtSlot(str)
    def _on_transcription_done(self, text: str) -> None:
        if text and self._settings.auto_insert:
            # Small delay so hotkey keys are fully released before pasting
            threading.Timer(0.2, insert_text, args=(text,)).start()
        self._status_changed.emit("inserted")
        # Reset to ready after a moment so the user sees the confirmation
        threading.Timer(2.0, lambda: self._status_changed.emit("ready")).start()

    # ------------------------------------------------------------------
    # Quit
    # ------------------------------------------------------------------

    @pyqtSlot()
    def _quit(self) -> None:
        self.shutdown()
        self._qapp.quit()

"""
Settings window – allows the user to configure hotkeys, language,
microphone and Whisper model size.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QKeySequenceEdit,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtGui import QKeySequence

from config.settings import LANGUAGES, LANGUAGE_CYCLE, Settings
from core.recorder import list_microphones

if TYPE_CHECKING:
    pass

WHISPER_MODELS = ["tiny", "base", "small", "medium", "large"]


class HotkeyEdit(QLineEdit):
    """Single-line editor that captures a key combination."""

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        # The parent's keyPressEvent signature uses QKeyEvent; we accept the
        # generic QEvent type here so the override works with PyQt6's type stubs.
        mods = event.modifiers()
        key = event.key()

        parts = []
        if mods & Qt.KeyboardModifier.ControlModifier:
            parts.append("ctrl")
        if mods & Qt.KeyboardModifier.AltModifier:
            parts.append("alt")
        if mods & Qt.KeyboardModifier.ShiftModifier:
            parts.append("shift")
        if mods & Qt.KeyboardModifier.MetaModifier:
            parts.append("win")

        ignore = {
            Qt.Key.Key_Control,
            Qt.Key.Key_Alt,
            Qt.Key.Key_Shift,
            Qt.Key.Key_Meta,
        }
        if key not in ignore:
            seq = QKeySequence(key).toString().lower()
            if seq:
                parts.append(seq)

        if parts:
            self.setText("+".join(parts))


class SettingsWindow(QDialog):
    """Modal settings dialog."""

    settings_saved = pyqtSignal(Settings)

    def __init__(self, settings: Settings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings = settings
        self.setWindowTitle("MyWhisper – Einstellungen / Settings")
        self.setMinimumWidth(420)
        self._build_ui()
        self._populate()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        # --- Hotkeys ---------------------------------------------------
        hk_group = QGroupBox("Hotkeys")
        hk_form = QFormLayout(hk_group)

        self._hk_record = HotkeyEdit()
        self._hk_record.setToolTip(
            "Klicken und gewünschte Tastenkombination drücken"
        )
        hk_form.addRow("Aufnahme starten/stoppen:", self._hk_record)

        self._hk_lang = HotkeyEdit()
        self._hk_lang.setToolTip(
            "Klicken und gewünschte Tastenkombination drücken"
        )
        hk_form.addRow("Sprache umschalten:", self._hk_lang)
        root.addWidget(hk_group)

        # --- Language --------------------------------------------------
        lang_group = QGroupBox("Standardsprache / Default Language")
        lang_layout = QHBoxLayout(lang_group)
        self._lang_combo = QComboBox()
        for code in LANGUAGE_CYCLE:
            self._lang_combo.addItem(LANGUAGES[code], code)
        lang_layout.addWidget(self._lang_combo)
        root.addWidget(lang_group)

        # --- Microphone ------------------------------------------------
        mic_group = QGroupBox("Mikrofon / Microphone")
        mic_layout = QHBoxLayout(mic_group)
        self._mic_combo = QComboBox()
        self._refresh_mics()
        mic_layout.addWidget(self._mic_combo)
        refresh_btn = QPushButton("↺")
        refresh_btn.setFixedWidth(30)
        refresh_btn.setToolTip("Geräteliste aktualisieren")
        refresh_btn.clicked.connect(self._refresh_mics)
        mic_layout.addWidget(refresh_btn)
        root.addWidget(mic_group)

        # --- Models ----------------------------------------------------
        model_group = QGroupBox("Whisper-Modelle")
        model_layout = QVBoxLayout(model_group)

        live_row = QHBoxLayout()
        live_row.addWidget(QLabel("Live (schnell):"))
        self._live_model_combo = QComboBox()
        for m in ["tiny", "base"]:
            self._live_model_combo.addItem(m)
        live_row.addWidget(self._live_model_combo)
        model_layout.addLayout(live_row)

        final_row = QHBoxLayout()
        final_row.addWidget(QLabel("Final (genau):"))
        self._final_model_combo = QComboBox()
        for m in WHISPER_MODELS:
            self._final_model_combo.addItem(m)
        final_row.addWidget(self._final_model_combo)
        model_layout.addLayout(final_row)

        model_layout.addWidget(
            QLabel("Live: tiny/base empfohlen ohne NVIDIA GPU")
        )
        root.addWidget(model_group)

        # --- Auto insert -----------------------------------------------
        self._auto_insert_cb = QCheckBox(
            "Text automatisch einfügen (Ctrl+V)"
        )
        root.addWidget(self._auto_insert_cb)

        self._live_transcription_cb = QCheckBox(
            "Laufende Erkennung und laufendes Einfügen aktivieren"
        )
        self._live_transcription_cb.setToolTip(
            "Während der Aufnahme werden stabile Zwischenstände laufend eingefügt."
        )
        root.addWidget(self._live_transcription_cb)

        self._emoji_mode_cb = QCheckBox(
            "Emoji-Modus (Text mit passenden Emojis anreichern 🎉)"
        )
        self._emoji_mode_cb.setToolTip(
            "Bekannte Schlüsselwörter im transkribierten Text werden mit passenden Emojis ergänzt."
        )
        root.addWidget(self._emoji_mode_cb)

        # --- Buttons ---------------------------------------------------
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Speichern / Save")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Abbrechen / Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        root.addLayout(btn_layout)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _refresh_mics(self) -> None:
        current_index = self._settings.microphone_index
        current_name = self._settings.microphone_name
        self._mic_combo.clear()
        self._mic_combo.addItem("System-Standard / Default", None)
        for mic in list_microphones():
            self._mic_combo.addItem(mic["name"], mic["index"])
        # Restore selection by index first, then by name as fallback.
        for i in range(self._mic_combo.count()):
            if self._mic_combo.itemData(i) == current_index:
                self._mic_combo.setCurrentIndex(i)
                return
        if current_name:
            for i in range(self._mic_combo.count()):
                if self._mic_combo.itemText(i) == current_name:
                    self._mic_combo.setCurrentIndex(i)
                    return

    def _populate(self) -> None:
        self._hk_record.setText(self._settings.hotkey_record)
        self._hk_lang.setText(self._settings.hotkey_language)

        for i in range(self._lang_combo.count()):
            if self._lang_combo.itemData(i) == self._settings.language:
                self._lang_combo.setCurrentIndex(i)

        for i in range(self._live_model_combo.count()):
            if self._live_model_combo.itemText(i) == self._settings.live_whisper_model:
                self._live_model_combo.setCurrentIndex(i)

        for i in range(self._final_model_combo.count()):
            if self._final_model_combo.itemText(i) == self._settings.final_whisper_model:
                self._final_model_combo.setCurrentIndex(i)

        self._auto_insert_cb.setChecked(self._settings.auto_insert)
        self._live_transcription_cb.setChecked(self._settings.live_transcription_enabled)
        self._emoji_mode_cb.setChecked(self._settings.emoji_mode_enabled)
        self._refresh_mics()

    def _save(self) -> None:
        self._settings.hotkey_record = self._hk_record.text().strip()
        self._settings.hotkey_language = self._hk_lang.text().strip()
        self._settings.language = self._lang_combo.currentData()
        self._settings.microphone_index = self._mic_combo.currentData()
        self._settings.microphone_name = None if self._mic_combo.currentIndex() == 0 else self._mic_combo.currentText()
        self._settings.live_whisper_model = self._live_model_combo.currentText()
        self._settings.final_whisper_model = self._final_model_combo.currentText()
        self._settings.auto_insert = self._auto_insert_cb.isChecked()
        self._settings.live_transcription_enabled = self._live_transcription_cb.isChecked()
        self._settings.emoji_mode_enabled = self._emoji_mode_cb.isChecked()
        self._settings.save()
        self.accept()
        QTimer.singleShot(0, lambda: self.settings_saved.emit(self._settings))

"""
History window showing recently recognized texts.
Allows user to view and re-insert previous transcriptions.
"""

from __future__ import annotations

from typing import Callable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel
)


class HistoryWindow(QDialog):
    """Modal dialog showing transcription history."""

    text_selected = pyqtSignal(str)  # Emitted when user selects a text to re-insert

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Transkriptions-Verlauf")
        self.setGeometry(100, 100, 600, 400)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Zuletzt erkannte Texte:")
        layout.addWidget(title)
        
        # History list
        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(self._on_item_selected)
        layout.addWidget(self._list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self._insert_btn = QPushButton("Einfügen")
        self._insert_btn.clicked.connect(self._on_insert)
        self._insert_btn.setEnabled(False)
        button_layout.addWidget(self._insert_btn)
        
        close_btn = QPushButton("Schließen")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # Connect selection changes
        self._list.itemSelectionChanged.connect(self._on_selection_changed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_history(self, history: list[str]) -> None:
        """Update the history list display."""
        self._list.clear()
        for text in reversed(history):  # Show most recent first
            if text.strip():  # Only add non-empty texts
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, text)
                self._list.addItem(item)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _on_selection_changed(self) -> None:
        """Enable insert button when something is selected."""
        self._insert_btn.setEnabled(len(self._list.selectedItems()) > 0)

    def _on_item_selected(self) -> None:
        """Handle double-click on history item."""
        self._on_insert()

    def _on_insert(self) -> None:
        """Emit selected text and close dialog."""
        selected = self._list.selectedItems()
        if selected:
            text = selected[0].text()
            self.text_selected.emit(text)
            self.close()

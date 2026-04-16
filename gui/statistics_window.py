"""Statistics window for recording usage metrics."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


class StatisticsWindow(QDialog):
    """Displays aggregates for day/week/month recording usage."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Aufnahme-Statistik")
        self.setGeometry(120, 120, 760, 520)

        layout = QVBoxLayout(self)
        header = QLabel("Statistik: erfolgreiche finale Transkriptionen")
        layout.addWidget(header)

        self._day_table = self._build_table("Tag")
        self._week_table = self._build_table("Woche")
        self._month_table = self._build_table("Monat")

        layout.addWidget(QLabel("Pro Tag"))
        layout.addWidget(self._day_table)
        layout.addWidget(QLabel("Pro Woche (Mo-So)"))
        layout.addWidget(self._week_table)
        layout.addWidget(QLabel("Pro Monat"))
        layout.addWidget(self._month_table)

        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        close_btn = QPushButton("Schließen")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

    def set_data(self, *, day_rows: list[dict], week_rows: list[dict], month_rows: list[dict]) -> None:
        self._fill_table(self._day_table, day_rows)
        self._fill_table(self._week_table, week_rows)
        self._fill_table(self._month_table, month_rows)

    def _build_table(self, period_label: str) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(
            [period_label, "Anzahl Starts", "Gesamt", "Durchschnitt"]
        )
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.verticalHeader().setVisible(False)
        return table

    def _fill_table(self, table: QTableWidget, rows: list[dict]) -> None:
        table.setRowCount(len(rows))
        for idx, row in enumerate(rows):
            table.setItem(idx, 0, QTableWidgetItem(str(row.get("period", ""))))
            table.setItem(idx, 1, QTableWidgetItem(str(int(row.get("count", 0)))))
            table.setItem(
                idx,
                2,
                QTableWidgetItem(self._format_seconds_hhmmss(float(row.get("total_seconds", 0.0)))),
            )
            table.setItem(
                idx,
                3,
                QTableWidgetItem(self._format_seconds_hhmmss(float(row.get("avg_seconds", 0.0)))),
            )

        header = table.horizontalHeader()
        header.setStretchLastSection(True)

    def _format_seconds_hhmmss(self, seconds: float) -> str:
        total = max(0, int(round(seconds)))
        hours = total // 3600
        minutes = (total % 3600) // 60
        secs = total % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

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

from config.localization import tr


class StatisticsWindow(QDialog):
    """Displays aggregates for day/week/month recording usage."""

    def __init__(self, parent=None, settings=None) -> None:
        super().__init__(parent)
        self._settings = settings
        self.setWindowTitle(tr("statistics_title", self._settings))
        self.setGeometry(120, 120, 760, 520)

        layout = QVBoxLayout(self)
        self._header = QLabel()
        layout.addWidget(self._header)

        self._day_table = self._build_table(tr("day", self._settings))
        self._week_table = self._build_table(tr("week", self._settings))
        self._month_table = self._build_table(tr("month", self._settings))

        self._day_label = QLabel()
        layout.addWidget(self._day_label)
        layout.addWidget(self._day_table)
        self._week_label = QLabel()
        layout.addWidget(self._week_label)
        layout.addWidget(self._week_table)
        self._month_label = QLabel()
        layout.addWidget(self._month_label)
        layout.addWidget(self._month_table)

        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        self._close_btn = QPushButton()
        self._close_btn.clicked.connect(self.close)
        button_layout.addWidget(self._close_btn)
        layout.addLayout(button_layout)
        self.retranslate_ui()

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

    def retranslate_ui(self) -> None:
        """Refresh UI strings for the current interface language."""
        self.setWindowTitle(tr("statistics_title", self._settings))
        self._header.setText(tr("statistics_header", self._settings))
        self._day_label.setText(tr("per_day", self._settings))
        self._week_label.setText(tr("per_week", self._settings))
        self._month_label.setText(tr("per_month", self._settings))
        self._close_btn.setText(tr("close", self._settings))
        self._day_table.setHorizontalHeaderLabels(
            [tr("day", self._settings), tr("starts", self._settings), tr("total", self._settings), tr("average", self._settings)]
        )
        self._week_table.setHorizontalHeaderLabels(
            [tr("week", self._settings), tr("starts", self._settings), tr("total", self._settings), tr("average", self._settings)]
        )
        self._month_table.setHorizontalHeaderLabels(
            [tr("month", self._settings), tr("starts", self._settings), tr("total", self._settings), tr("average", self._settings)]
        )

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

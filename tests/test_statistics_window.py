from __future__ import annotations

import pytest

from PyQt6.QtWidgets import QApplication

from gui.statistics_window import StatisticsWindow


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_statistics_window_renders_hhmmss_without_decimals(qapp):
    window = StatisticsWindow()
    window.set_data(
        day_rows=[
            {
                "period": "2026-04-16",
                "count": 2,
                "total_seconds": 3661.4,
                "avg_seconds": 1830.7,
            }
        ],
        week_rows=[],
        month_rows=[],
    )

    assert window._day_table.item(0, 2).text() == "01:01:01"
    assert window._day_table.item(0, 3).text() == "00:30:31"

    window.close()

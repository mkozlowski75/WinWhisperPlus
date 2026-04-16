from __future__ import annotations

from datetime import datetime

from core.statistics import StatisticsStore


def test_statistics_aggregates_day_week_month(tmp_path):
    path = tmp_path / "statistics.json"
    store = StatisticsStore(path=path, persist=True)

    store.record_session(started_at=datetime(2026, 4, 14, 9, 30), duration_seconds=10.0, language="de")
    store.record_session(started_at=datetime(2026, 4, 14, 12, 0), duration_seconds=20.0, language="de")
    store.record_session(started_at=datetime(2026, 4, 15, 8, 0), duration_seconds=30.0, language="en")

    day_rows = store.get_aggregates("day")
    assert day_rows[0]["period"] == "2026-04-15"
    assert day_rows[0]["count"] == 1
    assert day_rows[0]["total_seconds"] == 30.0
    assert day_rows[0]["avg_seconds"] == 30.0

    assert day_rows[1]["period"] == "2026-04-14"
    assert day_rows[1]["count"] == 2
    assert day_rows[1]["total_seconds"] == 30.0
    assert day_rows[1]["avg_seconds"] == 15.0

    week_rows = store.get_aggregates("week")
    assert len(week_rows) == 1
    assert week_rows[0]["period"] == "2026-W16"
    assert week_rows[0]["count"] == 3
    assert week_rows[0]["total_seconds"] == 60.0
    assert week_rows[0]["avg_seconds"] == 20.0

    month_rows = store.get_aggregates("month")
    assert len(month_rows) == 1
    assert month_rows[0]["period"] == "2026-04"
    assert month_rows[0]["count"] == 3
    assert month_rows[0]["total_seconds"] == 60.0
    assert month_rows[0]["avg_seconds"] == 20.0


def test_statistics_persistence_roundtrip(tmp_path):
    path = tmp_path / "statistics.json"
    store = StatisticsStore(path=path, persist=True)
    store.record_session(started_at=datetime(2026, 1, 10, 10, 0), duration_seconds=12.5, language="pl")

    reloaded = StatisticsStore(path=path, persist=True)
    month_rows = reloaded.get_aggregates("month")

    assert len(month_rows) == 1
    assert month_rows[0]["period"] == "2026-01"
    assert month_rows[0]["count"] == 1
    assert month_rows[0]["total_seconds"] == 12.5
    assert month_rows[0]["avg_seconds"] == 12.5

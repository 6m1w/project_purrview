"""Tests for daily digest module."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.digest import build_digest, _query_daily_counts


@pytest.fixture
def mock_storage():
    """Create a mock PurrviewStorage."""
    storage = MagicMock()
    return storage


def _make_execute_result(data):
    """Helper to build mock .execute() return."""
    result = MagicMock()
    result.data = data
    return result


class TestQueryDailyCounts:
    def test_groups_by_cat_and_activity(self, mock_storage):
        mock_storage.client.table.return_value.select.return_value.gte.return_value.lt.return_value.execute.return_value = _make_execute_result([
            {"cat_name": "大吉", "activity": "eating"},
            {"cat_name": "大吉", "activity": "eating"},
            {"cat_name": "大吉", "activity": "drinking"},
            {"cat_name": "小黑", "activity": "eating"},
        ])
        counts = _query_daily_counts(mock_storage, "2026-02-20", "2026-02-21")
        assert counts["大吉"]["eating"] == 2
        assert counts["大吉"]["drinking"] == 1
        assert counts["小黑"]["eating"] == 1

    def test_empty_result(self, mock_storage):
        mock_storage.client.table.return_value.select.return_value.gte.return_value.lt.return_value.execute.return_value = _make_execute_result([])
        counts = _query_daily_counts(mock_storage, "2026-02-20", "2026-02-21")
        assert counts == {}


class TestBuildDigest:
    def _setup_storage(self, mock_storage, yesterday_data, week_data):
        """Set up mock to return different data for two calls."""
        results = [
            _make_execute_result(yesterday_data),
            _make_execute_result(week_data),
        ]
        mock_storage.client.table.return_value.select.return_value.gte.return_value.lt.return_value.execute.side_effect = results

    def test_normal_day(self, mock_storage):
        self._setup_storage(
            mock_storage,
            yesterday_data=[
                {"cat_name": "大吉", "activity": "eating"},
                {"cat_name": "大吉", "activity": "eating"},
                {"cat_name": "小慢", "activity": "eating"},
                {"cat_name": "小慢", "activity": "eating"},
            ],
            week_data=[
                *[{"cat_name": "大吉", "activity": "eating"}] * 14,  # 2/day avg
                *[{"cat_name": "小慢", "activity": "eating"}] * 14,
            ],
        )
        target = datetime(2026, 2, 20, tzinfo=timezone.utc)
        digest = build_digest(mock_storage, target_date=target)

        assert digest["date"] == "2026-02-20"
        assert digest["total_eating"] == 4
        assert digest["cats"]["大吉"]["yesterday_eating"] == 2
        assert digest["cats"]["大吉"]["avg_eating"] == 2.0
        assert digest["cats"]["大吉"]["alert"] is None
        assert digest["cats"]["小慢"]["alert"] is None

    def test_no_eating_alert(self, mock_storage):
        self._setup_storage(
            mock_storage,
            yesterday_data=[],  # no events yesterday
            week_data=[
                *[{"cat_name": "小黑", "activity": "eating"}] * 14,  # 2/day avg
            ],
        )
        target = datetime(2026, 2, 20, tzinfo=timezone.utc)
        digest = build_digest(mock_storage, target_date=target)

        assert digest["cats"]["小黑"]["yesterday_eating"] == 0
        assert digest["cats"]["小黑"]["avg_eating"] == 2.0
        assert digest["cats"]["小黑"]["alert"] == "no_eating"

    def test_low_eating_alert(self, mock_storage):
        self._setup_storage(
            mock_storage,
            yesterday_data=[
                {"cat_name": "麻酱", "activity": "eating"},  # 1 yesterday
            ],
            week_data=[
                *[{"cat_name": "麻酱", "activity": "eating"}] * 21,  # 3/day avg
            ],
        )
        target = datetime(2026, 2, 20, tzinfo=timezone.utc)
        digest = build_digest(mock_storage, target_date=target)

        assert digest["cats"]["麻酱"]["yesterday_eating"] == 1
        assert digest["cats"]["麻酱"]["avg_eating"] == 3.0
        assert digest["cats"]["麻酱"]["alert"] == "low_eating"

    def test_no_alert_when_no_history(self, mock_storage):
        """No alert if 7-day average is also 0 (new system, no data yet)."""
        self._setup_storage(mock_storage, yesterday_data=[], week_data=[])
        target = datetime(2026, 2, 20, tzinfo=timezone.utc)
        digest = build_digest(mock_storage, target_date=target)

        for name in digest["cats"]:
            assert digest["cats"][name]["alert"] is None

    def test_all_cats_present(self, mock_storage):
        """All 5 known cats should appear in digest even with no data."""
        self._setup_storage(mock_storage, yesterday_data=[], week_data=[])
        target = datetime(2026, 2, 20, tzinfo=timezone.utc)
        digest = build_digest(mock_storage, target_date=target)

        from src.analyzer import CAT_NAMES
        assert set(digest["cats"].keys()) == set(CAT_NAMES)

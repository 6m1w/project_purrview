"""Tests for per-cat session tracker."""

import pytest

from src.analyzer import Activity, CatActivity, IdentifyResult
from src.tracker import FeedingSession, SessionTracker


@pytest.fixture
def tracker():
    return SessionTracker(idle_timeout=10)  # short timeout for tests


def _result(cats: list[tuple[str, str]], confidence: float = 0.95) -> IdentifyResult:
    """Helper to build IdentifyResult from (name, activity) tuples."""
    return IdentifyResult(
        cats_present=len(cats) > 0,
        cats=[CatActivity(name=n, activity=Activity(a)) for n, a in cats],
        confidence=confidence,
    )


class TestSessionStart:
    def test_eating_starts_session(self, tracker):
        completed = tracker.on_analysis(_result([("大吉", "eating")]), timestamp=100.0)
        assert completed == []
        assert "大吉" in tracker.sessions
        assert tracker.sessions["大吉"].activity == "eating"

    def test_drinking_starts_session(self, tracker):
        tracker.on_analysis(_result([("小黑", "drinking")]), timestamp=100.0)
        assert "小黑" in tracker.sessions
        assert tracker.sessions["小黑"].activity == "drinking"

    def test_present_does_not_start_session(self, tracker):
        tracker.on_analysis(_result([("大吉", "present")]), timestamp=100.0)
        assert "大吉" not in tracker.sessions


class TestSessionUpdate:
    def test_same_activity_updates_last_seen(self, tracker):
        tracker.on_analysis(_result([("大吉", "eating")]), timestamp=100.0)
        tracker.on_analysis(_result([("大吉", "eating")]), timestamp=110.0)
        assert tracker.sessions["大吉"].last_seen_at == 110.0

    def test_present_keeps_session_alive(self, tracker):
        tracker.on_analysis(_result([("大吉", "eating")]), timestamp=100.0)
        tracker.on_analysis(_result([("大吉", "present")]), timestamp=105.0)
        assert "大吉" in tracker.sessions
        assert tracker.sessions["大吉"].last_seen_at == 105.0
        assert tracker.sessions["大吉"].activity == "eating"  # unchanged


class TestSessionEnd:
    def test_idle_timeout_ends_session(self, tracker):
        tracker.on_analysis(_result([("大吉", "eating")]), timestamp=100.0)
        completed = tracker.check_idle(now=115.0)  # 15s > 10s timeout
        assert len(completed) == 1
        assert completed[0].cat_name == "大吉"
        assert completed[0].activity == "eating"
        assert "大吉" not in tracker.sessions

    def test_no_timeout_if_recent(self, tracker):
        tracker.on_analysis(_result([("大吉", "eating")]), timestamp=100.0)
        completed = tracker.check_idle(now=105.0)  # 5s < 10s timeout
        assert completed == []
        assert "大吉" in tracker.sessions

    def test_activity_change_ends_old_starts_new(self, tracker):
        tracker.on_analysis(_result([("大吉", "eating")]), timestamp=100.0)
        completed = tracker.on_analysis(_result([("大吉", "drinking")]), timestamp=110.0)
        assert len(completed) == 1
        assert completed[0].activity == "eating"
        assert tracker.sessions["大吉"].activity == "drinking"


class TestMultiCat:
    def test_two_cats_independent_sessions(self, tracker):
        tracker.on_analysis(
            _result([("大吉", "eating"), ("小黑", "drinking")]),
            timestamp=100.0,
        )
        assert "大吉" in tracker.sessions
        assert "小黑" in tracker.sessions
        assert tracker.sessions["大吉"].activity == "eating"
        assert tracker.sessions["小黑"].activity == "drinking"

    def test_one_cat_ends_other_continues(self, tracker):
        tracker.on_analysis(
            _result([("大吉", "eating"), ("小黑", "drinking")]),
            timestamp=100.0,
        )
        # Only 大吉 continues
        tracker.on_analysis(_result([("大吉", "eating")]), timestamp=108.0)
        # 小黑 times out
        completed = tracker.check_idle(now=115.0)
        assert len(completed) == 1
        assert completed[0].cat_name == "小黑"
        assert "大吉" in tracker.sessions


class TestFeedingSession:
    def test_session_tracks_frames(self, tracker):
        tracker.on_analysis(
            _result([("大吉", "eating")]),
            timestamp=100.0,
            frame_info={"filename": "frame1.jpg"},
        )
        tracker.on_analysis(
            _result([("大吉", "eating")]),
            timestamp=105.0,
            frame_info={"filename": "frame2.jpg"},
        )
        session = tracker.sessions["大吉"]
        assert len(session.frames) == 2
        assert session.frames[0]["filename"] == "frame1.jpg"

    def test_session_duration(self, tracker):
        tracker.on_analysis(_result([("大吉", "eating")]), timestamp=100.0)
        tracker.on_analysis(_result([("大吉", "eating")]), timestamp=160.0)
        session = tracker.sessions["大吉"]
        assert session.last_seen_at - session.started_at == 60.0

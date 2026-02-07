"""Tests for feeding event tracker."""

import time

import pytest

from src.analyzer import FrameAnalysis, FoodLevel
from src.tracker import FeedingState, FeedingTracker


@pytest.fixture
def tracker():
    return FeedingTracker(idle_timeout=2)  # short timeout for tests


class TestFeedingTracker:
    def test_initial_state_is_idle(self, tracker):
        assert tracker.get_state("bowl_1") == FeedingState.IDLE

    def test_motion_transitions_to_active(self, tracker):
        tracker.on_motion("bowl_1")
        assert tracker.get_state("bowl_1") == FeedingState.ACTIVE

    def test_analysis_with_eating_transitions_to_feeding(self, tracker):
        tracker.on_motion("bowl_1")
        analysis = FrameAnalysis(
            cat_detected=True,
            cat_name="Mochi",
            is_eating=True,
            food_level=FoodLevel.FULL,
            confidence=0.9,
        )
        tracker.on_analysis("bowl_1", analysis)
        assert tracker.get_state("bowl_1") == FeedingState.FEEDING

    def test_idle_timeout_completes_event(self, tracker):
        tracker.on_motion("bowl_1")
        analysis = FrameAnalysis(
            cat_detected=True,
            cat_name="Mochi",
            is_eating=True,
            food_level=FoodLevel.FULL,
            confidence=0.85,
        )
        tracker.on_analysis("bowl_1", analysis)

        # Manually set last_activity far in the past
        tracker.current_event["bowl_1"].last_activity_at = time.time() - 10

        completed = tracker.check_idle()
        assert len(completed) == 1
        bowl_id, event = completed[0]
        assert bowl_id == "bowl_1"
        assert event.cat_name == "Mochi"
        assert event.food_level_before == "full"
        assert tracker.get_state("bowl_1") == FeedingState.IDLE

    def test_multiple_bowls_independent(self, tracker):
        tracker.on_motion("bowl_1")
        tracker.on_motion("bowl_2")
        assert tracker.get_state("bowl_1") == FeedingState.ACTIVE
        assert tracker.get_state("bowl_2") == FeedingState.ACTIVE

    def test_food_level_tracking(self, tracker):
        tracker.on_motion("bowl_1")

        # First analysis: food is full
        tracker.on_analysis("bowl_1", FrameAnalysis(
            cat_detected=True, cat_name="Luna", is_eating=True,
            food_level=FoodLevel.FULL, confidence=0.8,
        ))
        # Second analysis: food decreased
        tracker.on_analysis("bowl_1", FrameAnalysis(
            cat_detected=True, cat_name="Luna", is_eating=True,
            food_level=FoodLevel.HALF, confidence=0.9,
        ))

        event = tracker.current_event["bowl_1"]
        assert event.food_level_before == "full"
        assert event.food_level_after == "1/2"
        assert event.confidence == 0.9  # max confidence

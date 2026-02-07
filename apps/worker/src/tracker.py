"""Feeding event state machine - groups frames into feeding events."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .analyzer import FrameAnalysis


class FeedingState(Enum):
    IDLE = "idle"
    ACTIVE = "active"       # motion detected, waiting for Gemini confirmation
    FEEDING = "feeding"     # Gemini confirmed cat is eating


@dataclass
class FeedingEvent:
    """Represents an ongoing or completed feeding event."""
    cat_name: Optional[str] = None
    bowl_id: Optional[str] = None
    started_at: float = 0.0
    last_activity_at: float = 0.0
    food_level_before: Optional[str] = None
    food_level_after: Optional[str] = None
    confidence: float = 0.0
    frame_analyses: list[FrameAnalysis] = field(default_factory=list)
    frame_urls: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


class FeedingTracker:
    """Tracks feeding state per bowl and groups frames into events."""

    def __init__(self, idle_timeout: int = 120):
        self.idle_timeout = idle_timeout
        self.state: dict[str, FeedingState] = {}          # bowl_id -> state
        self.current_event: dict[str, FeedingEvent] = {}  # bowl_id -> event

    def on_motion(self, bowl_id: str) -> None:
        """Called when motion is detected in a bowl's ROI."""
        current = self.state.get(bowl_id, FeedingState.IDLE)
        if current == FeedingState.IDLE:
            self.state[bowl_id] = FeedingState.ACTIVE
            self.current_event[bowl_id] = FeedingEvent(
                bowl_id=bowl_id,
                started_at=time.time(),
                last_activity_at=time.time(),
            )
        else:
            event = self.current_event.get(bowl_id)
            if event:
                event.last_activity_at = time.time()

    def on_analysis(self, bowl_id: str, analysis: FrameAnalysis) -> None:
        """Called when Gemini analysis completes for a bowl."""
        event = self.current_event.get(bowl_id)
        if not event:
            return

        event.frame_analyses.append(analysis)
        event.last_activity_at = time.time()

        if analysis.cat_detected and analysis.is_eating:
            self.state[bowl_id] = FeedingState.FEEDING
            if not event.cat_name and analysis.cat_name:
                event.cat_name = analysis.cat_name
            if not event.food_level_before and analysis.food_level:
                event.food_level_before = analysis.food_level.value
            # Always update "after" to latest
            if analysis.food_level:
                event.food_level_after = analysis.food_level.value
            event.confidence = max(event.confidence, analysis.confidence)
            if analysis.notes:
                event.notes.append(analysis.notes)

    def check_idle(self) -> list[tuple[str, FeedingEvent]]:
        """Check for bowls that have gone idle. Returns completed events."""
        completed = []
        now = time.time()

        for bowl_id, state in list(self.state.items()):
            if state == FeedingState.IDLE:
                continue
            event = self.current_event.get(bowl_id)
            if event and (now - event.last_activity_at) > self.idle_timeout:
                completed.append((bowl_id, event))
                self.state[bowl_id] = FeedingState.IDLE
                del self.current_event[bowl_id]

        return completed

    def get_state(self, bowl_id: str) -> FeedingState:
        """Get the current state of a bowl."""
        return self.state.get(bowl_id, FeedingState.IDLE)

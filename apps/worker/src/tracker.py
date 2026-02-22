"""Per-cat feeding session tracker.

Groups Gemini analysis results into feeding/drinking sessions.
Each cat is tracked independently with a simple state machine:
IDLE -> IN_SESSION (on eating/drinking) -> IDLE (after timeout).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .analyzer import Activity, IdentifyResult


@dataclass
class FeedingSession:
    """A feeding or drinking session for a single cat."""
    cat_name: str
    activity: str                       # "eating" or "drinking"
    started_at: float                   # unix timestamp
    last_seen_at: float                 # unix timestamp
    frames: list[dict] = field(default_factory=list)
    max_motion_score: float = 0.0


class SessionTracker:
    """Tracks per-cat feeding/drinking sessions.

    Rules:
    - eating/drinking -> starts or continues a session
    - present -> keeps existing session alive (resets idle timer) but doesn't start one
    - activity change (eating->drinking) -> ends old session, starts new one
    - 60s no detection -> session ends
    """

    def __init__(self, idle_timeout: int = 60):
        self.idle_timeout = idle_timeout
        self.sessions: dict[str, FeedingSession] = {}  # cat_name -> active session

    def on_analysis(
        self,
        result: IdentifyResult,
        timestamp: float,
        frame_info: dict | None = None,
    ) -> list[FeedingSession]:
        """Process a Gemini analysis result. Returns list of completed sessions.

        Args:
            result: Gemini IdentifyResult with per-cat activities
            timestamp: Frame timestamp (unix seconds)
            frame_info: Optional dict with frame metadata (filename, etc.)
        """
        completed: list[FeedingSession] = []

        for cat in result.cats:
            name = cat.name
            activity = cat.activity

            existing = self.sessions.get(name)

            if activity in (Activity.EATING, Activity.DRINKING):
                if existing and existing.activity != activity.value:
                    # Activity changed — end old session, start new one
                    completed.append(existing)
                    del self.sessions[name]
                    existing = None

                motion = frame_info.get("motion_score", 0) if frame_info else 0

                if existing:
                    # Continue existing session
                    existing.last_seen_at = timestamp
                    existing.max_motion_score = max(existing.max_motion_score, motion)
                    if frame_info:
                        existing.frames.append(frame_info)
                else:
                    # Start new session
                    session = FeedingSession(
                        cat_name=name,
                        activity=activity.value,
                        started_at=timestamp,
                        last_seen_at=timestamp,
                        max_motion_score=motion,
                    )
                    if frame_info:
                        session.frames.append(frame_info)
                    self.sessions[name] = session

            elif activity == Activity.PRESENT and existing:
                # Present keeps session alive but doesn't start one
                existing.last_seen_at = timestamp

        return completed

    def check_idle(self, now: float) -> list[FeedingSession]:
        """Check for sessions that have timed out. Returns completed sessions."""
        completed: list[FeedingSession] = []
        for name in list(self.sessions):
            session = self.sessions[name]
            if (now - session.last_seen_at) > self.idle_timeout:
                completed.append(session)
                del self.sessions[name]
        return completed

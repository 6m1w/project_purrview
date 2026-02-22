"""Supabase client wrapper for storing feeding sessions and uploading frames."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from supabase import Client, create_client

from .config import get_settings
from .tracker import FeedingSession


class PurrviewStorage:
    """Handles all Supabase interactions for the PurrView worker."""

    BUCKET = "purrview-frames"

    def __init__(self, client: Optional[Client] = None):
        if client is not None:
            self.client = client
        else:
            s = get_settings()
            self.client: Client = create_client(s.supabase_url, s.supabase_key)

    def get_cat_profiles(self) -> list[dict]:
        """Fetch all cat profiles with their reference photo URLs."""
        result = self.client.table("purrview_cats").select("*").execute()
        return result.data

    def upload_frame(self, frame_bytes: bytes, event_id: str) -> str:
        """Upload a frame image to Supabase Storage.

        Returns:
            Public URL of the uploaded frame.
        """
        filename = f"{event_id}/{uuid.uuid4().hex}.jpg"
        self.client.storage.from_(self.BUCKET).upload(
            filename,
            frame_bytes,
            {"content-type": "image/jpeg"},
        )
        return self.client.storage.from_(self.BUCKET).get_public_url(filename)

    def save_session(self, session: FeedingSession) -> str:
        """Save a completed feeding session to the database.

        Maps FeedingSession fields to purrview_feeding_events columns.

        Returns:
            The created event ID.
        """
        event_id = str(uuid.uuid4())
        duration = session.last_seen_at - session.started_at
        cat_id = self.resolve_cat_id(session.cat_name)

        self.client.table("purrview_feeding_events").insert(
            {
                "id": event_id,
                "cat_id": cat_id,
                "cat_name": session.cat_name,
                "activity": session.activity,
                "started_at": datetime.fromtimestamp(
                    session.started_at, tz=timezone.utc
                ).isoformat(),
                "ended_at": datetime.fromtimestamp(
                    session.last_seen_at, tz=timezone.utc
                ).isoformat(),
                "duration_seconds": round(duration, 1),
                "motion_score_max": session.max_motion_score or None,
                "confidence": None,
                "notes": None,
            }
        ).execute()
        return event_id

    def save_frame(
        self,
        event_id: str,
        frame_url: str,
        captured_at: datetime,
        analysis: Optional[dict] = None,
    ) -> None:
        """Save a frame record linked to a feeding event."""
        self.client.table("purrview_frames").insert(
            {
                "feeding_event_id": event_id,
                "captured_at": captured_at.isoformat(),
                "frame_url": frame_url,
                "analysis": analysis,
            }
        ).execute()

    def resolve_cat_id(self, cat_name: Optional[str]) -> Optional[str]:
        """Look up a cat's UUID by name."""
        if not cat_name:
            return None
        result = (
            self.client.table("purrview_cats")
            .select("id")
            .eq("name", cat_name)
            .limit(1)
            .execute()
        )
        return result.data[0]["id"] if result.data else None

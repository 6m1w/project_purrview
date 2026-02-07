"""Supabase client wrapper for storing events and uploading frames."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from supabase import create_client, Client

from .config import get_settings
from .tracker import FeedingEvent


class PurrviewStorage:
    """Handles all Supabase interactions for the PurrView worker."""

    BUCKET = "purrview-frames"

    def __init__(self):
        s = get_settings()
        self.client: Client = create_client(s.supabase_url, s.supabase_service_role_key)

    def get_cat_profiles(self) -> list[dict]:
        """Fetch all cat profiles with their reference photo URLs."""
        result = self.client.table("purrview_cats").select("*").execute()
        return result.data

    def get_active_bowls(self) -> list[dict]:
        """Fetch all active food bowl configurations."""
        result = (
            self.client.table("purrview_food_bowls")
            .select("*")
            .eq("is_active", True)
            .execute()
        )
        return result.data

    def upload_frame(self, frame_bytes: bytes, event_id: str) -> str:
        """Upload a frame image to Supabase Storage.

        Returns:
            Public URL of the uploaded frame
        """
        filename = f"{event_id}/{uuid.uuid4().hex}.jpg"
        self.client.storage.from_(self.BUCKET).upload(
            filename,
            frame_bytes,
            {"content-type": "image/jpeg"},
        )
        return self.client.storage.from_(self.BUCKET).get_public_url(filename)

    def save_feeding_event(
        self,
        event: FeedingEvent,
        cat_id: Optional[str] = None,
    ) -> str:
        """Save a completed feeding event to the database.

        Returns:
            The created event ID
        """
        event_id = str(uuid.uuid4())
        self.client.table("purrview_feeding_events").insert({
            "id": event_id,
            "cat_id": cat_id,
            "bowl_id": event.bowl_id,
            "started_at": datetime.fromtimestamp(event.started_at, tz=timezone.utc).isoformat(),
            "ended_at": datetime.fromtimestamp(event.last_activity_at, tz=timezone.utc).isoformat(),
            "food_level_before": event.food_level_before,
            "food_level_after": event.food_level_after,
            "confidence": event.confidence,
            "notes": "; ".join(event.notes) if event.notes else None,
        }).execute()
        return event_id

    def save_frame(
        self,
        event_id: str,
        frame_url: str,
        captured_at: datetime,
        analysis: Optional[dict] = None,
    ) -> None:
        """Save a frame record linked to a feeding event."""
        self.client.table("purrview_frames").insert({
            "feeding_event_id": event_id,
            "captured_at": captured_at.isoformat(),
            "frame_url": frame_url,
            "analysis": analysis,
        }).execute()

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

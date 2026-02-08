"""Standalone daily digest script — run via cron at end of day."""

from __future__ import annotations

from datetime import datetime, timezone

from .notifier import LarkNotifier
from .storage import PurrviewStorage


def run_digest() -> None:
    """Query today's feeding events and send a Lark daily digest."""
    notifier = LarkNotifier()
    if not notifier.enabled:
        print("[digest] Lark webhook not configured, skipping digest.")
        return

    storage = PurrviewStorage()
    today = datetime.now(tz=timezone.utc).date()
    date_str = today.isoformat()
    today_start = datetime(today.year, today.month, today.day, tzinfo=timezone.utc).isoformat()

    # Fetch today's events with cat name joined
    result = (
        storage.client.table("purrview_feeding_events")
        .select("*, purrview_cats(name)")
        .gte("started_at", today_start)
        .order("started_at", desc=True)
        .execute()
    )
    events = result.data

    print(f"[digest] Found {len(events)} feeding event(s) for {date_str}")

    # Extract cat_name from joined data for easier consumption
    for ev in events:
        cat_data = ev.get("purrview_cats")
        if cat_data and isinstance(cat_data, dict):
            ev["cat_name"] = cat_data.get("name", "Unknown")

    success = notifier.send_daily_digest(events, date_str)
    if success:
        print("[digest] Daily digest sent successfully.")
    else:
        print("[digest] Failed to send daily digest.")


if __name__ == "__main__":
    run_digest()

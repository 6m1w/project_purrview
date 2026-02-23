"""Supabase data retention: delete frames and events older than N days.

Cleans up:
1. Storage bucket objects (purrview-frames/) — the actual JPEG files
2. purrview_frames DB rows — frame metadata
3. purrview_feeding_events DB rows — event records

Usage:
    cd apps/worker
    python -m src.cleanup              # delete data older than 14 days
    python -m src.cleanup --days 30    # custom retention
    python -m src.cleanup --dry-run    # preview without deleting
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone

from .storage import PurrviewStorage


def run_cleanup(retention_days: int = 14, dry_run: bool = False) -> None:
    """Delete Supabase data older than retention_days."""
    storage = PurrviewStorage()
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=retention_days)
    cutoff_iso = cutoff.isoformat()

    print(f"[cleanup] Retention: {retention_days} days, cutoff: {cutoff.date()}")

    # 1. Find old events
    result = (
        storage.client.table("purrview_feeding_events")
        .select("id")
        .lt("started_at", cutoff_iso)
        .execute()
    )
    old_event_ids = [r["id"] for r in result.data]
    print(f"[cleanup] Found {len(old_event_ids)} events to delete")

    if not old_event_ids:
        print("[cleanup] Nothing to clean up")
        return

    if dry_run:
        print("[cleanup] Dry run — not deleting")
        return

    # 2. Delete storage objects (each event has a folder: {event_id}/*.jpg)
    deleted_files = 0
    for eid in old_event_ids:
        try:
            files = storage.client.storage.from_(storage.BUCKET).list(eid)
            if files:
                paths = [f"{eid}/{f['name']}" for f in files]
                storage.client.storage.from_(storage.BUCKET).remove(paths)
                deleted_files += len(paths)
        except Exception as e:
            print(f"[cleanup] Storage delete error for {eid}: {e}")

    print(f"[cleanup] Deleted {deleted_files} storage files")

    # 3. Delete frame DB rows
    storage.client.table("purrview_frames").delete().in_(
        "feeding_event_id", old_event_ids
    ).execute()
    print(f"[cleanup] Deleted frame records")

    # 4. Delete event DB rows
    storage.client.table("purrview_feeding_events").delete().in_(
        "id", old_event_ids
    ).execute()
    print(f"[cleanup] Deleted {len(old_event_ids)} event records")

    print("[cleanup] Done")


def main() -> None:
    parser = argparse.ArgumentParser(description="PurrView Supabase data cleanup")
    parser.add_argument("--days", type=int, default=14, help="Retention days (default: 14)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without deleting")
    args = parser.parse_args()
    run_cleanup(retention_days=args.days, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

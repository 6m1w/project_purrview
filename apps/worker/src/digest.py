"""Daily digest: per-cat feeding stats with anomaly detection and system stats.

Queries Supabase for yesterday's events, compares against 7-day rolling
average, and sends a Lark card with per-cat breakdown + anomaly flags
+ system status (Gemini calls, cost, worker health).

Usage:
    cd apps/worker
    python -m src.digest              # send digest for yesterday
    python -m src.digest --dry-run    # print stats without sending
"""

from __future__ import annotations

import argparse
import subprocess
from datetime import datetime, timedelta, timezone
from typing import Optional

from .analyzer import CAT_NAMES
from .notifier import LarkNotifier
from .storage import PurrviewStorage

# Gemini cost per call (16 images incl. refs, Gemini 2.5 Flash pricing)
GEMINI_COST_PER_CALL = 0.0026


def _query_daily_counts(
    storage: PurrviewStorage,
    date_start: str,
    date_end: str,
) -> dict[str, dict[str, int]]:
    """Query feeding event counts grouped by cat_name and activity for a date range.

    Returns:
        {cat_name: {"eating": N, "drinking": N}}
    """
    result = (
        storage.client.table("purrview_feeding_events")
        .select("cat_name, activity")
        .gte("started_at", date_start)
        .lt("started_at", date_end)
        .execute()
    )
    counts: dict[str, dict[str, int]] = {}
    for row in result.data:
        name = row.get("cat_name") or "Unknown"
        act = row.get("activity") or "eating"
        if name not in counts:
            counts[name] = {"eating": 0, "drinking": 0}
        if act in counts[name]:
            counts[name][act] += 1
    return counts


def _query_frame_count(
    storage: PurrviewStorage,
    date_start: str,
    date_end: str,
) -> int:
    """Count frames captured yesterday (proxy for Gemini API calls)."""
    result = (
        storage.client.table("purrview_frames")
        .select("id", count="exact")
        .gte("captured_at", date_start)
        .lt("captured_at", date_end)
        .execute()
    )
    return result.count or 0


def _get_worker_status() -> str:
    """Check if purrview-worker systemd service is active."""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "purrview-worker"],
            capture_output=True, text=True, timeout=5,
        )
        status = result.stdout.strip()
        return status if status else "unknown"
    except Exception:
        return "unknown"


def build_digest(
    storage: PurrviewStorage,
    target_date: Optional[datetime] = None,
) -> dict:
    """Build digest data: yesterday's counts vs 7-day average per cat + system stats.

    Returns:
        {
            "date": "2026-02-20",
            "cats": {
                "大吉": {
                    "yesterday_eating": 3,
                    "yesterday_drinking": 1,
                    "avg_eating": 2.8,
                    "avg_drinking": 0.9,
                    "alert": None | "no_eating" | "low_eating",
                },
                ...
            },
            "total_eating": 12,
            "total_drinking": 5,
            "system_stats": {
                "gemini_calls": 42,
                "estimated_cost": 0.11,
                "worker_status": "active",
            },
        }
    """
    if target_date is None:
        target_date = datetime.now(tz=timezone.utc) - timedelta(days=1)

    yesterday = target_date.date()
    date_str = yesterday.isoformat()

    # Yesterday's window
    y_start = datetime(yesterday.year, yesterday.month, yesterday.day, tzinfo=timezone.utc)
    y_end = y_start + timedelta(days=1)

    # 7-day window (excluding yesterday to avoid double counting)
    week_start = y_start - timedelta(days=7)

    yesterday_counts = _query_daily_counts(storage, y_start.isoformat(), y_end.isoformat())
    week_counts = _query_daily_counts(storage, week_start.isoformat(), y_start.isoformat())

    cats: dict[str, dict] = {}
    total_eating = 0
    total_drinking = 0

    for name in CAT_NAMES:
        yc = yesterday_counts.get(name, {"eating": 0, "drinking": 0})
        wc = week_counts.get(name, {"eating": 0, "drinking": 0})

        # 7-day average (may be fewer days if system just started)
        avg_eating = wc["eating"] / 7
        avg_drinking = wc["drinking"] / 7

        # Anomaly detection
        alert = None
        if yc["eating"] == 0 and avg_eating >= 1:
            alert = "no_eating"
        elif avg_eating >= 2 and yc["eating"] <= 1:
            alert = "low_eating"

        cats[name] = {
            "yesterday_eating": yc["eating"],
            "yesterday_drinking": yc["drinking"],
            "avg_eating": round(avg_eating, 1),
            "avg_drinking": round(avg_drinking, 1),
            "alert": alert,
        }
        total_eating += yc["eating"]
        total_drinking += yc["drinking"]

    # System stats: frame count as proxy for Gemini calls
    frame_count = _query_frame_count(storage, y_start.isoformat(), y_end.isoformat())
    # Each event has ~1 saved frame, but Gemini is called on every motion trigger.
    # Use total events (eating + drinking) + some overhead as rough call estimate.
    # More accurate: frames saved ≈ successful calls that found cats.
    # Total calls ≈ frames * ~3x (many calls find no cats and save no frame).
    estimated_calls = max(frame_count * 3, total_eating + total_drinking)
    estimated_cost = estimated_calls * GEMINI_COST_PER_CALL
    worker_status = _get_worker_status()

    return {
        "date": date_str,
        "cats": cats,
        "total_eating": total_eating,
        "total_drinking": total_drinking,
        "system_stats": {
            "gemini_calls": estimated_calls,
            "estimated_cost": round(estimated_cost, 2),
            "worker_status": worker_status,
        },
    }


def run_digest(dry_run: bool = False) -> None:
    """Build and send daily digest."""
    storage = PurrviewStorage()
    digest = build_digest(storage)

    date_str = digest["date"]
    cats = digest["cats"]
    sys_stats = digest.get("system_stats", {})

    print(f"[digest] Date: {date_str}")
    print(f"[digest] Total: {digest['total_eating']} eating, {digest['total_drinking']} drinking")
    print()
    print(f"  {'Cat':<6} {'Eat':>4} {'Avg':>5} {'Drink':>6} {'Avg':>5}  Alert")
    print(f"  {'-'*40}")
    for name in CAT_NAMES:
        c = cats[name]
        alert_str = ""
        if c["alert"] == "no_eating":
            alert_str = "🚨 NO EATING"
        elif c["alert"] == "low_eating":
            alert_str = "⚠️  LOW"
        print(
            f"  {name:<6} {c['yesterday_eating']:>4} {c['avg_eating']:>5} "
            f"{c['yesterday_drinking']:>6} {c['avg_drinking']:>5}  {alert_str}"
        )

    if sys_stats:
        print()
        print(f"  System: Gemini ~{sys_stats['gemini_calls']} calls, "
              f"~${sys_stats['estimated_cost']:.2f}, worker={sys_stats['worker_status']}")

    if dry_run:
        print("\n[digest] Dry run — not sending to Lark")
        return

    notifier = LarkNotifier()
    if not notifier.enabled:
        print("[digest] Lark webhook not configured, skipping.")
        return

    success = notifier.send_daily_digest(digest)
    if success:
        print("\n[digest] Sent to Lark.")
    else:
        print("\n[digest] Failed to send to Lark.")


def main() -> None:
    parser = argparse.ArgumentParser(description="PurrView daily digest")
    parser.add_argument("--dry-run", action="store_true", help="Print stats without sending")
    args = parser.parse_args()
    run_digest(dry_run=args.dry_run)


if __name__ == "__main__":
    main()

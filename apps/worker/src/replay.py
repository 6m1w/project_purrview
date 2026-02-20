"""Offline replay: run analyzer + tracker on captured data to verify sessions.

Usage:
    cd apps/worker
    python -m src.replay --date 2026-02-10 --limit 20    # quick test
    python -m src.replay --date 2026-02-10                # full day
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

from .analyzer import CatAnalyzer
from .label import _load_api_key
from .tracker import SessionTracker, FeedingSession


def replay(
    date: str,
    output_dir: str = "data",
    refs_dir: str = "data/refs",
    limit: int = 0,
    idle_timeout: int = 60,
    cooldown: int = 30,
    model: str = "gemini-2.5-flash",
) -> None:
    """Replay captured frames through analyzer + tracker."""
    date_dir = Path(output_dir) / date
    meta_path = date_dir / "gallery_meta.jsonl"

    if not meta_path.exists():
        print(f"[replay] Error: {meta_path} not found")
        sys.exit(1)

    # Load metadata, filter to motion frames
    entries: list[dict] = []
    with open(meta_path) as f:
        for line in f:
            if line.strip():
                e = json.loads(line)
                if e.get("motion_score", 0) > 5000:
                    entries.append(e)

    entries.sort(key=lambda e: e["timestamp"])
    print(f"[replay] Date: {date}, motion frames: {len(entries)}")

    if limit > 0:
        entries = entries[:limit]
        print(f"[replay] Limited to {limit} frames")

    # Init analyzer + tracker
    api_key = _load_api_key()
    analyzer = CatAnalyzer(api_key=api_key, refs_dir=Path(refs_dir), model=model)
    tracker = SessionTracker(idle_timeout=idle_timeout)

    all_completed: list[FeedingSession] = []
    last_call_ts = 0.0
    errors = 0
    calls = 0

    for i, entry in enumerate(entries):
        fname = entry["filename"]
        img_path = date_dir / fname
        if not img_path.exists():
            continue

        # Parse timestamp to unix seconds
        ts = datetime.fromisoformat(entry["timestamp"]).timestamp()

        # Check idle before each frame (using frame timestamp, not wall clock)
        completed = tracker.check_idle(now=ts)
        all_completed.extend(completed)
        for s in completed:
            _print_session(s, tag="END")

        # Apply cooldown (based on frame timestamps)
        if (ts - last_call_ts) < cooldown:
            continue
        last_call_ts = ts

        # Analyze frame
        frame_bytes = img_path.read_bytes()
        try:
            result = analyzer.analyze_frame(frame_bytes)
            calls += 1
            cats_str = ", ".join(f"{c.name}:{c.activity.value}" for c in result.cats) or "(none)"
            print(f"  [{i+1}/{len(entries)}] {fname} -> {cats_str}")

            completed = tracker.on_analysis(
                result, timestamp=ts, frame_info={"filename": fname, "timestamp": ts}
            )
            all_completed.extend(completed)
            for s in completed:
                _print_session(s, tag="SWITCH")

        except Exception as exc:
            errors += 1
            print(f"  [{i+1}/{len(entries)}] ERR {fname}: {exc}")

        time.sleep(0.3)  # rate limit

    # Flush remaining sessions
    final = tracker.check_idle(now=float("inf"))
    all_completed.extend(final)
    for s in final:
        _print_session(s, tag="FLUSH")

    # Summary
    print(f"\n{'='*60}")
    print(f"[replay] Sessions detected: {len(all_completed)}")
    print(f"[replay] Gemini calls: {calls}")
    print(f"[replay] Errors: {errors}")
    if all_completed:
        print(f"\n{'Cat':<8} {'Activity':<10} {'Duration':>8} {'Frames':>7}")
        print("-" * 37)
        for s in all_completed:
            duration = s.last_seen_at - s.started_at
            print(f"  {s.cat_name:<6} {s.activity:<10} {duration:>6.0f}s  {len(s.frames):>5}")


def _print_session(session: FeedingSession, tag: str = "") -> None:
    """Print a session event."""
    duration = session.last_seen_at - session.started_at
    print(
        f"  [{tag}] {session.cat_name} {session.activity} "
        f"({duration:.0f}s, {len(session.frames)} frames)"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay captured data through analyzer + tracker")
    parser.add_argument("--date", required=True, help="Date directory (YYYY-MM-DD)")
    parser.add_argument("--output", default="data", help="Base data directory")
    parser.add_argument("--refs", default="data/refs", help="Reference photos directory")
    parser.add_argument("--limit", type=int, default=0, help="Max motion frames (0=all)")
    parser.add_argument("--idle-timeout", type=int, default=60, help="Session idle timeout (seconds)")
    parser.add_argument("--cooldown", type=int, default=30, help="Seconds between Gemini calls")
    parser.add_argument("--model", default="gemini-2.5-flash", help="Gemini model")
    args = parser.parse_args()
    replay(args.date, args.output, args.refs, args.limit, args.idle_timeout, args.cooldown, args.model)


if __name__ == "__main__":
    main()

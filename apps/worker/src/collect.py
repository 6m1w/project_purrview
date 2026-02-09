"""Data collection tool - captures frames from RTMP for manual annotation.

Usage:
    cd apps/worker
    python -m src.collect                    # default: 1 hour, save to data/
    python -m src.collect --duration 300     # 5 minutes
    python -m src.collect --interval 5       # 1 frame per 5 seconds
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

from .capture import CAPTURE_HEIGHT, CAPTURE_WIDTH, capture_frames
from .config import get_settings

MOTION_THRESHOLD = 1000
THUMB_WIDTH = 220
THUMB_HEIGHT = 124


def compute_motion_score(current: np.ndarray, previous: np.ndarray | None) -> int:
    """Compute a simple motion score by frame differencing.

    Returns the number of pixels that changed significantly between frames.
    """
    if previous is None:
        return 0
    diff = cv2.absdiff(current, previous)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 25, 255, cv2.THRESH_BINARY)
    return int(cv2.countNonZero(thresh))


def _ensure_gallery_html(out: Path) -> None:
    """Create gallery.html symlink if it doesn't exist."""
    gallery = out / "gallery.html"
    target = Path("/var/www/purrview-data/gallery.html")
    if not gallery.exists() and target.exists():
        gallery.symlink_to(target)


def run_collection(
    duration: int = 3600,
    interval: int = 2,
    output_dir: str = "data",
) -> None:
    """Capture frames from RTMP stream and save with motion metadata.

    Writes thumbnails and metadata incrementally so the gallery page
    can display new frames in real time.

    Args:
        duration: How long to collect in seconds
        interval: Seconds between frame captures
        output_dir: Base output directory
    """
    cfg = get_settings()

    # Organize by date: data/2026-02-08/
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out = Path(output_dir) / today
    out.mkdir(parents=True, exist_ok=True)

    thumb_dir = out / "thumbs"
    thumb_dir.mkdir(exist_ok=True)

    meta_path = out / "gallery_meta.jsonl"
    _ensure_gallery_html(out)

    print(f"[collect] Capturing from {cfg.rtmp_url}", flush=True)
    print(f"[collect] Interval: {interval}s, Duration: {duration}s", flush=True)
    print(f"[collect] Output: {out}/", flush=True)
    print(f"[collect] Resolution: {CAPTURE_WIDTH}x{CAPTURE_HEIGHT}", flush=True)
    print(flush=True)

    prev_frame: np.ndarray | None = None
    frame_count = 0
    motion_frames = 0
    start_time = time.time()

    try:
        meta_file = open(meta_path, "a")

        for frame in capture_frames(cfg.rtmp_url, fps_interval=interval):
            elapsed = time.time() - start_time
            if elapsed >= duration:
                break

            ts = datetime.now(timezone.utc)
            motion_score = compute_motion_score(frame, prev_frame)
            prev_frame = frame.copy()

            # Save full frame as JPEG
            filename = f"{ts.strftime('%H%M%S')}_{frame_count:05d}.jpg"
            filepath = out / filename
            cv2.imwrite(str(filepath), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])

            # Save thumbnail
            thumb = cv2.resize(frame, (THUMB_WIDTH, THUMB_HEIGHT))
            cv2.imwrite(str(thumb_dir / filename), thumb, [cv2.IMWRITE_JPEG_QUALITY, 70])

            has_motion = motion_score > MOTION_THRESHOLD
            if has_motion:
                motion_frames += 1

            # Append metadata line (JSONL for incremental writes)
            entry = {
                "filename": filename,
                "timestamp": ts.isoformat(),
                "motion_score": motion_score,
                "has_motion": has_motion,
            }
            meta_file.write(json.dumps(entry) + "\n")
            meta_file.flush()

            frame_count += 1

            # Progress every 10 frames
            if frame_count % 10 == 0:
                pct = elapsed / duration * 100
                print(
                    f"[collect] {frame_count} frames | "
                    f"motion={motion_score:,} | "
                    f"{motion_frames} with motion | "
                    f"{pct:.0f}% done",
                    flush=True,
                )

    except KeyboardInterrupt:
        print("\n[collect] Stopped by user")
    finally:
        meta_file.close()

    print(f"\n[collect] Done!", flush=True)
    print(f"  Total frames:  {frame_count}", flush=True)
    print(f"  With motion:   {motion_frames}", flush=True)
    print(f"  Output dir:    {out}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="PurrView data collection tool")
    parser.add_argument("--duration", type=int, default=3600, help="Collection duration in seconds (default: 3600)")
    parser.add_argument("--interval", type=int, default=2, help="Seconds between frames (default: 2)")
    parser.add_argument("--output", type=str, default="data", help="Output directory (default: data/)")
    args = parser.parse_args()

    run_collection(
        duration=args.duration,
        interval=args.interval,
        output_dir=args.output,
    )


if __name__ == "__main__":
    main()

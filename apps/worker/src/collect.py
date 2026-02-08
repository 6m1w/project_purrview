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


def run_collection(
    duration: int = 3600,
    interval: int = 2,
    output_dir: str = "data",
) -> None:
    """Capture frames from RTMP stream and save with motion metadata.

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

    print(f"[collect] Capturing from {cfg.rtmp_url}")
    print(f"[collect] Interval: {interval}s, Duration: {duration}s")
    print(f"[collect] Output: {out}/")
    print(f"[collect] Resolution: {CAPTURE_WIDTH}x{CAPTURE_HEIGHT}")
    print()

    prev_frame: np.ndarray | None = None
    metadata: list[dict] = []
    frame_count = 0
    motion_frames = 0
    start_time = time.time()

    try:
        for frame in capture_frames(cfg.rtmp_url, fps_interval=interval):
            elapsed = time.time() - start_time
            if elapsed >= duration:
                break

            ts = datetime.now(timezone.utc)
            motion_score = compute_motion_score(frame, prev_frame)
            prev_frame = frame.copy()

            # Save every frame as JPEG
            filename = f"{ts.strftime('%H%M%S')}_{frame_count:05d}.jpg"
            filepath = out / filename
            cv2.imwrite(str(filepath), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])

            has_motion = motion_score > 1000  # rough threshold for "interesting"
            if has_motion:
                motion_frames += 1

            metadata.append({
                "filename": filename,
                "timestamp": ts.isoformat(),
                "motion_score": motion_score,
                "has_motion": has_motion,
            })

            frame_count += 1

            # Progress every 10 frames
            if frame_count % 10 == 0:
                pct = elapsed / duration * 100
                print(
                    f"[collect] {frame_count} frames | "
                    f"motion={motion_score:,} | "
                    f"{motion_frames} with motion | "
                    f"{pct:.0f}% done"
                )

    except KeyboardInterrupt:
        print("\n[collect] Stopped by user")

    # Save metadata
    meta_path = out / "metadata.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n[collect] Done!")
    print(f"  Total frames:  {frame_count}")
    print(f"  With motion:   {motion_frames}")
    print(f"  Output dir:    {out}")
    print(f"  Metadata:      {meta_path}")


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

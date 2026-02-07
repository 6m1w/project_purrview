"""PurrView worker entry point - orchestrates capture → detect → analyze → store."""

from __future__ import annotations

import time
from datetime import datetime, timezone

import cv2
import numpy as np

from .analyzer import CatAnalyzer
from .capture import capture_frames
from .config import ROI, get_settings
from .detector import MotionDetector
from .storage import PurrviewStorage
from .tracker import FeedingTracker


def encode_frame_jpeg(frame: np.ndarray, quality: int = 85) -> bytes:
    """Encode a BGR frame to JPEG bytes."""
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return buf.tobytes()


def run() -> None:
    """Main processing loop."""
    print("[main] PurrView worker starting...")

    storage = PurrviewStorage()
    analyzer = CatAnalyzer()
    cfg = get_settings()
    tracker = FeedingTracker(idle_timeout=cfg.idle_timeout)

    # Load bowl configs
    bowls = storage.get_active_bowls()
    if not bowls:
        print("[main] No active food bowls configured. Exiting.")
        return

    bowl_rois: dict[str, ROI] = {}
    detectors: dict[str, MotionDetector] = {}
    for bowl in bowls:
        bowl_id = bowl["id"]
        bowl_rois[bowl_id] = ROI(bowl["roi_x1"], bowl["roi_y1"], bowl["roi_x2"], bowl["roi_y2"])
        detectors[bowl_id] = MotionDetector()

    print(f"[main] Monitoring {len(bowls)} bowl(s): {[b['id'] for b in bowls]}")

    # Load cat profiles for Gemini context
    cat_profiles = storage.get_cat_profiles()
    print(f"[main] Loaded {len(cat_profiles)} cat profile(s)")

    # Track last Gemini call time per bowl (cooldown)
    last_gemini_call: dict[str, float] = {}

    # Main loop
    for frame in capture_frames(cfg.rtmp_url):
        now = time.time()

        for bowl_id, roi in bowl_rois.items():
            motion_detected, pixel_count = detectors[bowl_id].detect(frame, roi)

            if motion_detected:
                tracker.on_motion(bowl_id)

                # Check cooldown before calling Gemini
                last_call = last_gemini_call.get(bowl_id, 0)
                if (now - last_call) >= cfg.motion_cooldown:
                    last_gemini_call[bowl_id] = now
                    frame_bytes = encode_frame_jpeg(frame)
                    bowl_name = next(
                        (b["name"] for b in bowls if b["id"] == bowl_id),
                        bowl_id,
                    )

                    try:
                        analysis = analyzer.analyze_frame(
                            frame_bytes, cat_profiles, bowl_name
                        )
                        tracker.on_analysis(bowl_id, analysis)
                        print(
                            f"[main] Bowl {bowl_id}: "
                            f"cat={analysis.cat_name}, eating={analysis.is_eating}, "
                            f"food={analysis.food_level}, conf={analysis.confidence:.2f}"
                        )
                    except Exception as e:
                        print(f"[main] Gemini error for bowl {bowl_id}: {e}")

        # Check for completed feeding events
        completed = tracker.check_idle()
        for bowl_id, event in completed:
            print(f"[main] Feeding event completed at bowl {bowl_id}: cat={event.cat_name}")
            try:
                cat_id = storage.resolve_cat_id(event.cat_name)
                event_id = storage.save_feeding_event(event, cat_id)
                print(f"[main] Saved event {event_id}")
            except Exception as e:
                print(f"[main] Failed to save event: {e}")


if __name__ == "__main__":
    run()

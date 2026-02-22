"""PurrView worker entry point — capture → motion → analyze → track → store."""

from __future__ import annotations

import time
from pathlib import Path

import cv2
import numpy as np

from .analyzer import CatAnalyzer
from .capture import capture_frames
from .collect import compute_motion_score
from .config import get_settings
from .notifier import LarkNotifier
from .storage import PurrviewStorage
from .tracker import FeedingSession, SessionTracker


def encode_frame_jpeg(frame: np.ndarray, quality: int = 85) -> bytes:
    """Encode a BGR frame to JPEG bytes."""
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return buf.tobytes()


def _upload_first_frame(session: FeedingSession, storage: PurrviewStorage, event_id: str) -> str | None:
    """Upload the first captured frame of a session to Supabase Storage."""
    for f in session.frames:
        if f.get("frame_bytes"):
            try:
                url = storage.upload_frame(f["frame_bytes"], event_id)
                print(f"[main] Uploaded frame -> {url[:80]}...")
                return url
            except Exception as e:
                print(f"[main] Frame upload failed: {e}")
                return None
    return None


def _handle_completed(
    session: FeedingSession,
    storage: PurrviewStorage,
    notifier: LarkNotifier,
) -> None:
    """Save a completed session to Supabase and send a Lark notification."""
    duration = session.last_seen_at - session.started_at
    print(
        f"[main] Session complete: {session.cat_name} {session.activity} "
        f"({duration:.0f}s, {len(session.frames)} frames)"
    )

    # Filter out single-detection hallucinations (0s duration = only 1 Gemini hit)
    if duration < 1:
        print(f"[main] Skipping short session (likely hallucination)")
        return
    event_id = None
    image_url = None
    try:
        event_id = storage.save_session(session)
        print(f"[main] Saved event {event_id}")
        image_url = _upload_first_frame(session, storage, event_id)
    except Exception as e:
        print(f"[main] Failed to save session: {e}")

    notifier.send_feeding_alert(session, image_url=image_url)


def run() -> None:
    """Main processing loop."""
    print("[main] PurrView worker starting...")

    cfg = get_settings()
    storage = PurrviewStorage()
    analyzer = CatAnalyzer(
        api_key=cfg.gemini_api_key,
        refs_dir=Path(cfg.refs_dir),
        model=cfg.gemini_model,
    )
    notifier = LarkNotifier()
    tracker = SessionTracker(idle_timeout=cfg.idle_timeout)

    if notifier.enabled:
        print("[main] Lark notifications enabled")
    else:
        print("[main] Lark notifications disabled (no webhook URL)")

    print(
        f"[main] Config: motion_threshold={cfg.motion_threshold}, "
        f"cooldown={cfg.motion_cooldown}s, idle_timeout={cfg.idle_timeout}s"
    )

    prev_frame: np.ndarray | None = None
    last_gemini_call: float = 0

    for frame in capture_frames(cfg.rtmp_url):
        now = time.time()

        # 1. Simple frame-diff motion detection
        motion_score = compute_motion_score(frame, prev_frame)
        prev_frame = frame.copy()

        if motion_score > cfg.motion_threshold:
            # 2. Gemini cooldown check
            if (now - last_gemini_call) >= cfg.motion_cooldown:
                last_gemini_call = now
                frame_bytes = encode_frame_jpeg(frame)

                try:
                    result = analyzer.analyze_frame(frame_bytes)
                    if result.cats_present:
                        frame_info = {"timestamp": now, "frame_bytes": frame_bytes, "motion_score": motion_score}
                        completed = tracker.on_analysis(result, now, frame_info)
                        for session in completed:
                            _handle_completed(session, storage, notifier)

                        cats = ", ".join(
                            f"{c.name}({c.activity.value})" for c in result.cats
                        )
                        print(
                            f"[main] Gemini: {cats} "
                            f"(conf={result.confidence:.2f}, motion={motion_score})"
                        )
                    else:
                        print(f"[main] Gemini: no cats (motion={motion_score})")

                except Exception as e:
                    print(f"[main] Gemini error: {e}")

        # 3. Check for idle sessions
        completed = tracker.check_idle(now)
        for session in completed:
            _handle_completed(session, storage, notifier)


if __name__ == "__main__":
    run()

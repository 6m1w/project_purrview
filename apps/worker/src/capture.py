"""RTMP stream capture via ffmpeg subprocess."""

from __future__ import annotations

import subprocess
import time
from typing import Generator

import numpy as np

from .config import get_settings

# Output resolution after ffmpeg scale (original is 2560x1440)
CAPTURE_WIDTH = 1280
CAPTURE_HEIGHT = 720


def create_ffmpeg_process(rtmp_url: str, fps_interval: int | None = None) -> subprocess.Popen:
    """Start ffmpeg process to read RTMP stream and output raw frames to stdout.

    Args:
        rtmp_url: RTMP stream URL
        fps_interval: Seconds between frames (default: from settings)
    """
    interval = fps_interval or get_settings().frame_interval
    vf = f"fps=1/{interval},scale={CAPTURE_WIDTH}:{CAPTURE_HEIGHT}"
    cmd = [
        "ffmpeg",
        "-i", rtmp_url,
        "-an",                    # no audio
        "-vf", vf,
        "-f", "rawvideo",
        "-pix_fmt", "bgr24",
        "-loglevel", "error",
        "-",                      # output to stdout
    ]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def capture_frames(
    rtmp_url: str,
    fps_interval: int | None = None,
) -> Generator[np.ndarray, None, None]:
    """Yield frames from an RTMP stream via ffmpeg.

    Each frame is scaled to CAPTURE_WIDTH x CAPTURE_HEIGHT.

    Args:
        rtmp_url: RTMP stream URL
        fps_interval: Override frame interval (seconds)

    Yields:
        numpy array (BGR, 1280x720) for each captured frame
    """
    frame_size = CAPTURE_WIDTH * CAPTURE_HEIGHT * 3

    while True:
        process = create_ffmpeg_process(rtmp_url, fps_interval)
        try:
            while True:
                raw = process.stdout.read(frame_size)
                if len(raw) != frame_size:
                    break
                frame = np.frombuffer(raw, dtype=np.uint8).reshape(
                    (CAPTURE_HEIGHT, CAPTURE_WIDTH, 3)
                )
                yield frame
        except Exception as e:
            print(f"[capture] Stream error: {e}")
        finally:
            process.kill()
            process.wait()

        print("[capture] Stream disconnected, reconnecting in 5s...")
        time.sleep(5)

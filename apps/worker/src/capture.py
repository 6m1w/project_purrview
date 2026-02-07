"""RTMP stream capture via ffmpeg subprocess."""

from __future__ import annotations

import subprocess
import time
from typing import Generator

import cv2
import numpy as np

from .config import get_settings


def create_ffmpeg_process(rtmp_url: str) -> subprocess.Popen:
    """Start ffmpeg process to read RTMP stream and output raw frames to stdout."""
    cmd = [
        "ffmpeg",
        "-i", rtmp_url,
        "-an",                    # no audio
        "-vf", f"fps=1/{get_settings().frame_interval}",  # extract 1 frame per N seconds
        "-f", "rawvideo",
        "-pix_fmt", "bgr24",
        "-loglevel", "error",
        "-",                      # output to stdout
    ]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def capture_frames(
    rtmp_url: str,
    width: int = 1920,
    height: int = 1080,
) -> Generator[np.ndarray, None, None]:
    """Yield frames from an RTMP stream via ffmpeg.

    Args:
        rtmp_url: RTMP stream URL
        width: Expected frame width
        height: Expected frame height

    Yields:
        numpy array (BGR) for each captured frame
    """
    frame_size = width * height * 3  # BGR = 3 channels

    while True:
        process = create_ffmpeg_process(rtmp_url)
        try:
            while True:
                raw = process.stdout.read(frame_size)
                if len(raw) != frame_size:
                    break
                frame = np.frombuffer(raw, dtype=np.uint8).reshape((height, width, 3))
                yield frame
        except Exception as e:
            print(f"[capture] Stream error: {e}")
        finally:
            process.kill()
            process.wait()

        print("[capture] Stream disconnected, reconnecting in 5s...")
        time.sleep(5)

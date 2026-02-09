"""RTMP stream capture via ffmpeg subprocess."""

from __future__ import annotations

import select
import subprocess
import time
from typing import Generator

import numpy as np

from .config import get_settings

# Output resolution after ffmpeg scale (original is 2560x1440)
CAPTURE_WIDTH = 1280
CAPTURE_HEIGHT = 720

# Timeout for detecting a stalled stream (seconds)
READ_TIMEOUT = 30


def create_ffmpeg_process(rtmp_url: str, fps_interval: int | None = None) -> subprocess.Popen:
    """Start ffmpeg process to read RTMP stream and output raw frames to stdout.

    Args:
        rtmp_url: RTMP stream URL
        fps_interval: Seconds between frames (default: from settings)
    """
    interval = fps_interval or get_settings().frame_interval
    vf = f"fps=1/{interval},scale={CAPTURE_WIDTH}:{CAPTURE_HEIGHT}"
    # rw_timeout: microseconds; abort if no data for 30s at network level
    rw_timeout = str(READ_TIMEOUT * 1_000_000)
    cmd = [
        "ffmpeg",
        "-rw_timeout", rw_timeout,
        "-i", rtmp_url,
        "-an",                    # no audio
        "-vf", vf,
        "-f", "rawvideo",
        "-pix_fmt", "bgr24",
        "-loglevel", "error",
        "-",                      # output to stdout
    ]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _read_exact(pipe, size: int, timeout: float) -> bytes:
    """Read exactly `size` bytes from pipe with a per-read timeout.

    Raises TimeoutError if no data arrives within `timeout` seconds.
    """
    buf = bytearray()
    while len(buf) < size:
        ready, _, _ = select.select([pipe], [], [], timeout)
        if not ready:
            raise TimeoutError(f"No data for {timeout}s")
        chunk = pipe.read(size - len(buf))
        if not chunk:
            break
        buf.extend(chunk)
    return bytes(buf)


def capture_frames(
    rtmp_url: str,
    fps_interval: int | None = None,
) -> Generator[np.ndarray, None, None]:
    """Yield frames from an RTMP stream via ffmpeg.

    Each frame is scaled to CAPTURE_WIDTH x CAPTURE_HEIGHT.
    Automatically reconnects on stream stalls or disconnects.

    Args:
        rtmp_url: RTMP stream URL
        fps_interval: Override frame interval (seconds)

    Yields:
        numpy array (BGR, 1280x720) for each captured frame
    """
    frame_size = CAPTURE_WIDTH * CAPTURE_HEIGHT * 3
    # Allow more time for the first frame (connection + keyframe wait)
    first_frame_timeout = READ_TIMEOUT * 3
    interval = fps_interval or get_settings().frame_interval
    frame_timeout = max(READ_TIMEOUT, interval * 3)

    while True:
        process = create_ffmpeg_process(rtmp_url, fps_interval)
        first = True
        try:
            while True:
                timeout = first_frame_timeout if first else frame_timeout
                raw = _read_exact(process.stdout, frame_size, timeout)
                first = False
                if len(raw) != frame_size:
                    break
                frame = np.frombuffer(raw, dtype=np.uint8).reshape(
                    (CAPTURE_HEIGHT, CAPTURE_WIDTH, 3)
                )
                yield frame
        except TimeoutError as e:
            print(f"[capture] Stream stalled: {e}")
        except Exception as e:
            print(f"[capture] Stream error: {e}")
        finally:
            process.kill()
            process.wait()

        print("[capture] Stream disconnected, reconnecting in 5s...")
        time.sleep(5)

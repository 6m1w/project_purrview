"""Tests for motion detector."""

import numpy as np
import pytest

from src.config import ROI
from src.detector import MotionDetector


@pytest.fixture
def detector():
    return MotionDetector(threshold=100)


@pytest.fixture
def roi():
    return ROI(x1=100, y1=100, x2=300, y2=300)


def make_frame(width=400, height=400, color=(0, 0, 0)):
    """Create a solid-color test frame."""
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    frame[:] = color
    return frame


class TestMotionDetector:
    def test_no_motion_on_static_frames(self, detector, roi):
        """Static frames should not trigger motion after background stabilizes."""
        frame = make_frame()
        # Feed several frames to stabilize background model
        for _ in range(10):
            detected, _ = detector.detect(frame, roi)
        # After stabilization, no motion
        detected, count = detector.detect(frame, roi)
        assert not detected
        assert count == 0

    def test_motion_detected_on_change(self, detector, roi):
        """A sudden change in the ROI should trigger motion detection."""
        bg_frame = make_frame()
        # Stabilize background
        for _ in range(10):
            detector.detect(bg_frame, roi)

        # Introduce a bright rectangle in the ROI
        changed_frame = make_frame()
        changed_frame[150:250, 150:250] = (255, 255, 255)
        detected, count = detector.detect(changed_frame, roi)
        assert detected
        assert count > 100

    def test_reset_clears_background(self, detector, roi):
        """Reset should clear the learned background model."""
        frame = make_frame(color=(128, 128, 128))
        for _ in range(10):
            detector.detect(frame, roi)
        detector.reset()
        # After reset, first frame triggers some transient detection
        # but a new stable frame sequence should calm down
        for _ in range(10):
            detector.detect(frame, roi)
        detected, _ = detector.detect(frame, roi)
        assert not detected

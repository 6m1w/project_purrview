"""OpenCV MOG2 motion detection in food bowl ROI regions."""

from __future__ import annotations

import cv2
import numpy as np

from .config import ROI, get_settings


class MotionDetector:
    """Detects motion in food bowl regions using MOG2 background subtraction."""

    def __init__(self, threshold: int | None = None):
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=50,
            detectShadows=True,
        )
        self.threshold = threshold or get_settings().motion_threshold
        # Morphological kernel for noise removal
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

    def detect(self, frame: np.ndarray, roi: ROI) -> tuple[bool, int]:
        """Check if there is motion in the given ROI.

        Args:
            frame: Full camera frame (BGR)
            roi: Region of interest to check

        Returns:
            Tuple of (motion_detected: bool, pixel_count: int)
        """
        cropped = roi.crop(frame)
        fg_mask = self.bg_subtractor.apply(cropped)

        # Remove shadows (MOG2 marks shadows as 127, foreground as 255)
        _, fg_mask = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)

        # Morphological operations to reduce noise
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, self.kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, self.kernel)

        pixel_count = cv2.countNonZero(fg_mask)
        return pixel_count > self.threshold, pixel_count

    def reset(self) -> None:
        """Reset the background model."""
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=50,
            detectShadows=True,
        )

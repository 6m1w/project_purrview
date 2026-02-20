"""Tests for the main pipeline orchestration."""

from unittest.mock import MagicMock, patch

from src.main import _handle_completed, encode_frame_jpeg
from src.tracker import FeedingSession

import numpy as np


class TestEncodeFrameJpeg:
    def test_returns_bytes(self):
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        result = encode_frame_jpeg(frame)
        assert isinstance(result, bytes)
        # JPEG magic bytes
        assert result[:2] == b"\xff\xd8"

    def test_respects_quality(self):
        frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        low_q = encode_frame_jpeg(frame, quality=10)
        high_q = encode_frame_jpeg(frame, quality=95)
        assert len(low_q) < len(high_q)


class TestHandleCompleted:
    def test_saves_and_notifies(self):
        session = FeedingSession(
            cat_name="大吉",
            activity="eating",
            started_at=1000.0,
            last_seen_at=1300.0,
        )
        storage = MagicMock()
        storage.save_session.return_value = "event-uuid"
        notifier = MagicMock()

        _handle_completed(session, storage, notifier)

        storage.save_session.assert_called_once_with(session)
        notifier.send_feeding_alert.assert_called_once_with(session, image_url=None)

    def test_saves_and_uploads_frame(self):
        session = FeedingSession(
            cat_name="大吉",
            activity="eating",
            started_at=1000.0,
            last_seen_at=1300.0,
            frames=[{"timestamp": 1000.0, "frame_bytes": b"jpeg-data"}],
        )
        storage = MagicMock()
        storage.save_session.return_value = "event-uuid"
        storage.upload_frame.return_value = "https://example.com/frame.jpg"
        notifier = MagicMock()

        _handle_completed(session, storage, notifier)

        storage.upload_frame.assert_called_once_with(b"jpeg-data", "event-uuid")
        notifier.send_feeding_alert.assert_called_once_with(
            session, image_url="https://example.com/frame.jpg"
        )

    def test_notifies_even_if_storage_fails(self):
        session = FeedingSession(
            cat_name="小黑",
            activity="drinking",
            started_at=2000.0,
            last_seen_at=2060.0,
        )
        storage = MagicMock()
        storage.save_session.side_effect = Exception("DB down")
        notifier = MagicMock()

        _handle_completed(session, storage, notifier)

        # Notification still sent even when storage fails (no image)
        notifier.send_feeding_alert.assert_called_once_with(session, image_url=None)

    def test_prints_session_info(self, capsys):
        session = FeedingSession(
            cat_name="松花",
            activity="eating",
            started_at=1000.0,
            last_seen_at=1120.0,
            frames=[{"timestamp": 1000.0}, {"timestamp": 1060.0}],
        )
        storage = MagicMock()
        storage.save_session.return_value = "evt-123"
        notifier = MagicMock()

        _handle_completed(session, storage, notifier)

        output = capsys.readouterr().out
        assert "松花" in output
        assert "eating" in output
        assert "120s" in output
        assert "2 frames" in output

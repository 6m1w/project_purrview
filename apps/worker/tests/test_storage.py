"""Tests for Supabase storage module."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.storage import PurrviewStorage
from src.tracker import FeedingSession


@pytest.fixture
def mock_client():
    """Create a mock Supabase client."""
    client = MagicMock()
    # Chain: client.table("x").insert({}).execute()
    client.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data=[{}]
    )
    # Chain: client.table("x").select("*").execute()
    client.table.return_value.select.return_value.execute.return_value = MagicMock(
        data=[]
    )
    # Chain: client.table("x").select("id").eq("name", x).limit(1).execute()
    client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[]
    )
    return client


@pytest.fixture
def storage(mock_client):
    return PurrviewStorage(client=mock_client)


@pytest.fixture
def sample_session():
    return FeedingSession(
        cat_name="大吉",
        activity="eating",
        started_at=1000.0,
        last_seen_at=1300.0,
        frames=[{"timestamp": 1000.0}, {"timestamp": 1150.0}],
    )


class TestSaveSession:
    def test_inserts_with_correct_fields(self, storage, mock_client, sample_session):
        event_id = storage.save_session(sample_session)

        assert isinstance(event_id, str)
        assert len(event_id) == 36  # UUID format

        call_args = mock_client.table.return_value.insert.call_args
        row = call_args[0][0]

        assert row["cat_name"] == "大吉"
        assert row["activity"] == "eating"
        assert row["duration_seconds"] == 300.0
        assert row["started_at"].endswith("+00:00")
        assert row["ended_at"].endswith("+00:00")

    def test_resolves_cat_id(self, storage, mock_client, sample_session):
        # Make resolve_cat_id return a UUID
        mock_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[{"id": "cat-uuid-123"}]
        )
        storage.save_session(sample_session)

        call_args = mock_client.table.return_value.insert.call_args
        row = call_args[0][0]
        assert row["cat_id"] == "cat-uuid-123"

    def test_cat_id_none_when_not_found(self, storage, mock_client, sample_session):
        storage.save_session(sample_session)

        call_args = mock_client.table.return_value.insert.call_args
        row = call_args[0][0]
        assert row["cat_id"] is None


class TestResolveCatId:
    def test_returns_none_for_empty_name(self, storage):
        assert storage.resolve_cat_id(None) is None
        assert storage.resolve_cat_id("") is None

    def test_returns_id_when_found(self, storage, mock_client):
        mock_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[{"id": "uuid-abc"}]
        )
        assert storage.resolve_cat_id("大吉") == "uuid-abc"

    def test_returns_none_when_not_found(self, storage, mock_client):
        mock_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[]
        )
        assert storage.resolve_cat_id("UnknownCat") is None


class TestGetCatProfiles:
    def test_returns_data(self, storage, mock_client):
        mock_client.table.return_value.select.return_value.execute.return_value = (
            MagicMock(data=[{"id": "1", "name": "大吉"}])
        )
        profiles = storage.get_cat_profiles()
        assert len(profiles) == 1
        assert profiles[0]["name"] == "大吉"


class TestUploadFrame:
    def test_returns_public_url(self, storage, mock_client):
        mock_client.storage.from_.return_value.get_public_url.return_value = (
            "https://example.com/frame.jpg"
        )
        url = storage.upload_frame(b"jpeg-data", "event-123")
        assert url == "https://example.com/frame.jpg"
        mock_client.storage.from_.return_value.upload.assert_called_once()

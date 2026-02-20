"""Tests for Lark webhook notifier."""

from unittest.mock import MagicMock, patch

import pytest

from src.notifier import LarkNotifier
from src.tracker import FeedingSession


class TestLarkNotifierEnabled:
    def test_disabled_when_no_url(self):
        notifier = LarkNotifier(webhook_url="")
        assert notifier.enabled is False

    def test_enabled_when_url_set(self):
        notifier = LarkNotifier(webhook_url="https://open.feishu.cn/hook/test")
        assert notifier.enabled is True

    def test_send_is_noop_when_disabled(self):
        notifier = LarkNotifier(webhook_url="")
        session = FeedingSession(
            cat_name="Mochi", activity="eating", started_at=1000, last_seen_at=1420,
        )
        assert notifier.send_feeding_alert(session) is False


class TestLarkNotifierCards:
    def test_feeding_card_structure(self):
        notifier = LarkNotifier(webhook_url="https://open.feishu.cn/hook/test")
        session = FeedingSession(
            cat_name="Mochi",
            activity="eating",
            started_at=1000.0,
            last_seen_at=1420.0,
        )

        with patch("src.notifier.httpx.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"code": 0}
            mock_post.return_value = mock_resp

            result = notifier.send_feeding_alert(session)

        assert result is True
        call_args = mock_post.call_args
        payload = call_args.kwargs.get("json") or call_args[1].get("json") or call_args[0][1]

        assert payload["msg_type"] == "interactive"
        header = payload["card"]["header"]
        assert "Mochi" in header["title"]["content"]
        assert header["template"] == "green"

    def test_post_success(self):
        notifier = LarkNotifier(webhook_url="https://open.feishu.cn/hook/test")
        payload = {"msg_type": "text", "content": {"text": "test"}}

        with patch("src.notifier.httpx.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"code": 0}
            mock_post.return_value = mock_resp

            assert notifier._post_to_lark(payload) is True

    def test_post_failure_handled(self):
        notifier = LarkNotifier(webhook_url="https://open.feishu.cn/hook/test")
        payload = {"msg_type": "text", "content": {"text": "test"}}

        with patch("src.notifier.httpx.post", side_effect=Exception("connection error")):
            assert notifier._post_to_lark(payload) is False

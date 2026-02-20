"""Lark (Feishu) webhook notifier for feeding alerts and daily digests."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import httpx

from .config import get_settings
from .tracker import FeedingSession


class LarkNotifier:
    """Sends feeding alerts and daily digests to Lark via webhook."""

    def __init__(self, webhook_url: Optional[str] = None):
        if webhook_url is not None:
            self.webhook_url = webhook_url
        else:
            self.webhook_url = get_settings().lark_webhook_url

    @property
    def enabled(self) -> bool:
        return bool(self.webhook_url)

    def send_feeding_alert(
        self,
        session: FeedingSession,
    ) -> bool:
        """Send a real-time feeding alert card to Lark."""
        if not self.enabled:
            return False

        cat = session.cat_name or "Unknown cat"
        activity = session.activity
        duration = (session.last_seen_at - session.started_at) / 60
        started = datetime.fromtimestamp(session.started_at, tz=timezone.utc)
        ended = datetime.fromtimestamp(session.last_seen_at, tz=timezone.utc)
        time_range = f"{started.strftime('%H:%M')} - {ended.strftime('%H:%M')}"
        emoji = "💧" if activity == "drinking" else "🍽️"
        verb = "drank water" if activity == "drinking" else "ate"

        card = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "template": "green" if activity == "eating" else "blue",
                    "title": {"tag": "plain_text", "content": f"{emoji} {cat} just {verb}!"},
                },
                "elements": [
                    {
                        "tag": "div",
                        "fields": [
                            {
                                "is_short": True,
                                "text": {"tag": "lark_md", "content": f"**Cat**\n{cat}"},
                            },
                            {
                                "is_short": True,
                                "text": {"tag": "lark_md", "content": f"**Activity**\n{activity}"},
                            },
                        ],
                    },
                    {
                        "tag": "div",
                        "fields": [
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**Duration**\n{duration:.1f} min",
                                },
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**Frames**\n{len(session.frames)}",
                                },
                            },
                        ],
                    },
                    {"tag": "hr"},
                    {
                        "tag": "note",
                        "elements": [
                            {"tag": "plain_text", "content": time_range},
                        ],
                    },
                ],
            },
        }
        return self._post_to_lark(card)

    def send_daily_digest(
        self,
        events: list[dict],
        date_str: str,
    ) -> bool:
        """Send a daily digest summary card to Lark."""
        if not self.enabled:
            return False

        # Aggregate per-cat stats
        cat_stats: dict[str, dict] = {}
        for ev in events:
            cat_name = ev.get("cat_name") or ev.get("purrview_cats", {}).get("name", "Unknown")
            if cat_name not in cat_stats:
                cat_stats[cat_name] = {"count": 0, "total_duration": 0.0}
            cat_stats[cat_name]["count"] += 1
            started = ev.get("started_at", "")
            ended = ev.get("ended_at", "")
            if started and ended:
                try:
                    t0 = datetime.fromisoformat(started)
                    t1 = datetime.fromisoformat(ended)
                    cat_stats[cat_name]["total_duration"] += (t1 - t0).total_seconds() / 60
                except (ValueError, TypeError):
                    pass

        total_feedings = len(events)
        cats_fed = len(cat_stats)

        # Build per-cat breakdown
        breakdown_lines = []
        for name, stats in sorted(cat_stats.items()):
            breakdown_lines.append(
                f"**{name}**: {stats['count']} meal(s), ~{stats['total_duration']:.0f} min"
            )
        breakdown = "\n".join(breakdown_lines) if breakdown_lines else "No feedings recorded"

        card = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "template": "blue",
                    "title": {
                        "tag": "plain_text",
                        "content": f"📊 PurrView Daily - {date_str}",
                    },
                },
                "elements": [
                    {
                        "tag": "div",
                        "fields": [
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**Total feedings**\n{total_feedings}",
                                },
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**Cats fed**\n{cats_fed}/5",
                                },
                            },
                        ],
                    },
                    {"tag": "hr"},
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": breakdown},
                    },
                    {"tag": "hr"},
                    {
                        "tag": "note",
                        "elements": [
                            {"tag": "plain_text", "content": "PurrView Daily Digest"},
                        ],
                    },
                ],
            },
        }
        return self._post_to_lark(card)

    def _post_to_lark(self, payload: dict) -> bool:
        """POST a card payload to the Lark webhook. Returns True on success."""
        try:
            resp = httpx.post(self.webhook_url, json=payload, timeout=10)
            data = resp.json()
            if data.get("code") != 0:
                print(f"[notifier] Lark API error: {data}")
                return False
            return True
        except Exception as e:
            print(f"[notifier] Failed to send to Lark: {e}")
            return False

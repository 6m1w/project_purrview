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
        image_url: Optional[str] = None,
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

        elements: list[dict] = []
        elements.extend([
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
        ])

        # Image link (if available)
        if image_url:
            elements.append({
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "📷 View Photo"},
                        "type": "primary",
                        "url": image_url,
                    },
                ],
            })

        elements.append({
            "tag": "note",
            "elements": [
                {"tag": "plain_text", "content": time_range},
            ],
        })

        card = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "template": "green" if activity == "eating" else "blue",
                    "title": {"tag": "plain_text", "content": f"{emoji} {cat} just {verb}!"},
                },
                "elements": elements,
            },
        }
        return self._post_to_lark(card)

    def send_daily_digest(self, digest: dict) -> bool:
        """Send a daily digest card with per-cat stats and anomaly flags.

        Args:
            digest: Output of digest.build_digest() containing date, cats, totals.
        """
        if not self.enabled:
            return False

        date_str = digest["date"]
        cats = digest["cats"]
        total_eating = digest["total_eating"]
        total_drinking = digest["total_drinking"]

        # Build per-cat table
        header_line = "Cat       Eat  (avg)   Drink (avg)"
        table_lines = [header_line]
        alerts: list[str] = []

        from .analyzer import CAT_NAMES
        for name in CAT_NAMES:
            c = cats.get(name, {})
            ye = c.get("yesterday_eating", 0)
            ae = c.get("avg_eating", 0)
            yd = c.get("yesterday_drinking", 0)
            ad = c.get("avg_drinking", 0)
            alert = c.get("alert")

            flag = "  "
            if alert == "no_eating":
                flag = "🚨"
                alerts.append(f"🚨 **{name}** 昨天未检测到进食")
            elif alert == "low_eating":
                flag = "⚠️"
                alerts.append(f"⚠️ **{name}** 昨天进食明显减少")

            table_lines.append(f"{flag} {name}    {ye}   ({ae})     {yd}   ({ad})")

        table_md = "```\n" + "\n".join(table_lines) + "\n```"

        # Choose header color based on alerts
        has_red = any(c.get("alert") == "no_eating" for c in cats.values())
        has_yellow = any(c.get("alert") == "low_eating" for c in cats.values())
        if has_red:
            template = "red"
            title = f"🚨 PurrView Daily — {date_str}"
        elif has_yellow:
            template = "orange"
            title = f"⚠️ PurrView Daily — {date_str}"
        else:
            template = "blue"
            title = f"📊 PurrView Daily — {date_str}"

        elements: list[dict] = [
            {
                "tag": "div",
                "fields": [
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"**Total eating**\n{total_eating}",
                        },
                    },
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"**Total drinking**\n{total_drinking}",
                        },
                    },
                ],
            },
            {"tag": "hr"},
            {
                "tag": "div",
                "text": {"tag": "lark_md", "content": table_md},
            },
        ]

        if alerts:
            elements.append({"tag": "hr"})
            elements.append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": "\n".join(alerts)},
            })

        elements.append({
            "tag": "note",
            "elements": [
                {"tag": "plain_text", "content": "PurrView Daily Digest · (avg) = 7-day rolling average"},
            ],
        })

        card = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "template": template,
                    "title": {"tag": "plain_text", "content": title},
                },
                "elements": elements,
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

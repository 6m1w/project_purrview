"""Lark (Feishu) webhook notifier for feeding alerts and daily digests."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional

import httpx

from .config import get_settings
from .tracker import FeedingSession

DASHBOARD_URL = "https://purrview.dev/dashboard"

# Per-cat emoji for visual distinction in digest
CAT_EMOJI: dict[str, str] = {
    "大吉": "🍊",
    "小慢": "🎨",
    "小黑": "🖤",
    "麻酱": "🟤",
    "松花": "🐯",
}


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
        frames = len(session.frames)
        tz_beijing = timezone(timedelta(hours=8))
        started = datetime.fromtimestamp(session.started_at, tz=tz_beijing)
        ended = datetime.fromtimestamp(session.last_seen_at, tz=tz_beijing)
        time_range = f"{started.strftime('%H:%M')} - {ended.strftime('%H:%M')}"
        emoji = "💧" if activity == "drinking" else "🍽️"
        verb = "drank water" if activity == "drinking" else "ate"

        # Compact summary line: time · duration · frames
        summary = f"⏱ {time_range}  ·  {duration:.1f} min  ·  {frames} frames"

        elements: list[dict] = [
            {
                "tag": "div",
                "text": {"tag": "lark_md", "content": summary},
            },
            {"tag": "hr"},
        ]

        # Action buttons
        actions: list[dict] = []
        if image_url:
            actions.append({
                "tag": "button",
                "text": {"tag": "plain_text", "content": "📷 View Photo"},
                "type": "primary",
                "url": image_url,
            })
        actions.append({
            "tag": "button",
            "text": {"tag": "plain_text", "content": "📊 Dashboard"},
            "type": "default",
            "url": DASHBOARD_URL,
        })
        elements.append({"tag": "action", "actions": actions})

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
        """Send a daily digest card with per-cat stats, system stats, and anomaly flags.

        Args:
            digest: Output of digest.build_digest() containing date, cats, totals,
                    and optional system_stats dict.
        """
        if not self.enabled:
            return False

        date_str = digest["date"]
        cats = digest["cats"]
        total_eating = digest["total_eating"]
        total_drinking = digest["total_drinking"]
        system_stats = digest.get("system_stats", {})

        # Build per-cat lines with emoji
        alerts: list[str] = []
        cat_lines: list[str] = []

        from .analyzer import CAT_NAMES
        for name in CAT_NAMES:
            c = cats.get(name, {})
            ye = c.get("yesterday_eating", 0)
            ae = c.get("avg_eating", 0)
            yd = c.get("yesterday_drinking", 0)
            ad = c.get("avg_drinking", 0)
            alert = c.get("alert")

            em = CAT_EMOJI.get(name, "🐱")
            flag = ""
            if alert == "no_eating":
                flag = " 🚨"
                alerts.append(f"🚨 **{name}** 昨天未检测到进食")
            elif alert == "low_eating":
                flag = " ⚠️"
                alerts.append(f"⚠️ **{name}** 昨天进食明显减少")

            cat_lines.append(
                f"{em} **{name}**{flag}  ·  Eat: {ye} ({ae})  ·  Drink: {yd} ({ad})"
            )

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
            # Totals
            {
                "tag": "div",
                "fields": [
                    {
                        "is_short": True,
                        "text": {"tag": "lark_md", "content": f"**Total Eating**\n{total_eating}"},
                    },
                    {
                        "is_short": True,
                        "text": {"tag": "lark_md", "content": f"**Total Drinking**\n{total_drinking}"},
                    },
                ],
            },
            {"tag": "hr"},
            # Per-cat breakdown
            {
                "tag": "div",
                "text": {"tag": "lark_md", "content": "\n".join(cat_lines)},
            },
        ]

        # Alert section
        if alerts:
            elements.append({"tag": "hr"})
            elements.append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": "\n".join(alerts)},
            })

        # System stats section
        if system_stats:
            gemini_calls = system_stats.get("gemini_calls", 0)
            cost = system_stats.get("estimated_cost", 0)
            worker_status = system_stats.get("worker_status", "unknown")

            sys_line = (
                f"🤖 Gemini: **{gemini_calls}** calls · "
                f"~**${cost:.2f}**  ·  Worker: **{worker_status}**"
            )
            elements.append({"tag": "hr"})
            elements.append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": sys_line},
            })

        # Dashboard button + footer
        elements.append({
            "tag": "action",
            "actions": [{
                "tag": "button",
                "text": {"tag": "plain_text", "content": "📊 Open Dashboard"},
                "type": "primary",
                "url": DASHBOARD_URL,
            }],
        })
        elements.append({
            "tag": "note",
            "elements": [
                {"tag": "plain_text", "content": "PurrView Daily · (avg) = 7-day rolling average"},
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

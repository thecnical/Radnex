"""Headless Daemon & Background Webhook Reporting for Radnex.

Dispatches structured event payloads (findings, attack surface changes,
hunt completions) to external webhooks (Discord, Slack, or generic HTTP endpoints).
"""

from __future__ import annotations

import asyncio
import json
import logging
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger("radnex.webhook")


def format_webhook_payload(event_type: str, data: dict[str, Any], url: str) -> dict[str, Any]:
    """Format payload according to endpoint type (Discord, Slack, or generic)."""
    title = f"Radnex Alert: {event_type.upper()}"
    desc = data.get("summary") or data.get("message") or json.dumps(data, indent=2)

    # Discord Webhook format
    if "discord.com" in url or "discordapp.com" in url:
        color = 0x00FF88  # Green accent
        if "critical" in str(data).lower() or "high" in str(data).lower():
            color = 0xFF0033  # Red alert
        elif "warning" in str(data).lower():
            color = 0xFFAA00  # Amber
        return {
            "username": "Radnex Autonomous Agent",
            "embeds": [
                {
                    "title": title,
                    "description": desc[:2000],
                    "color": color,
                    "footer": {"text": "Radnex Security Assessment Engine"},
                }
            ],
        }

    # Slack Webhook format
    if "slack.com" in url:
        return {
            "text": f"*{title}*\n```{desc[:3000]}```",
        }

    # Generic JSON POST
    return {
        "agent": "radnex",
        "event": event_type,
        "data": data,
    }


def send_webhook_sync(url: str, event_type: str, data: dict[str, Any], timeout: float = 10.0) -> bool:
    """Send webhook synchronously."""
    if not url:
        return False
    payload = format_webhook_payload(event_type, data, url)
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Radnex-Agent/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.status < 300
    except Exception as exc:
        logger.debug("Webhook delivery failed: %s", exc)
        return False


async def dispatch_webhook(url: str | None, event_type: str, data: dict[str, Any]) -> None:
    """Asynchronously dispatch a webhook notification without blocking the agent turn."""
    if not url:
        return
    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, send_webhook_sync, url, event_type, data)
    except Exception as exc:
        logger.debug("Failed to dispatch async webhook: %s", exc)

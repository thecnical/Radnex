"""Regression suite for Headless Daemon & Background Webhook Reporting.

Run: python tests/test_webhook.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from radnex.webhook import format_webhook_payload

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, extra: str = "") -> None:
    RESULTS.append((name, ok, extra))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {extra}")


def test_payload_formatting() -> None:
    discord_url = "https://discord.com/api/webhooks/123/abc"
    slack_url = "https://hooks.slack.com/services/123/abc"
    generic_url = "https://api.mycompany.com/webhook"

    d_payload = format_webhook_payload("finding", {"summary": "SQL Injection found"}, discord_url)
    check("webhook: discord payload has embeds", "embeds" in d_payload and len(d_payload["embeds"]) > 0)

    s_payload = format_webhook_payload("finding", {"summary": "SQL Injection found"}, slack_url)
    check("webhook: slack payload has text", "text" in s_payload and "SQL Injection" in s_payload["text"])

    g_payload = format_webhook_payload("finding", {"summary": "SQL Injection found"}, generic_url)
    check("webhook: generic payload has event", g_payload.get("event") == "finding")


def main() -> None:
    test_payload_formatting()

    passed = sum(1 for _, ok, _ in RESULTS if ok)
    failed = sum(1 for _, ok, _ in RESULTS if not ok)
    print(f"\n{passed}/{len(RESULTS)} passed" + (f" — {failed} FAILED" if failed else ""))
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()

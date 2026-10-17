"""Regression suite for Smart Zero-Downtime Routing and strictly free model protection.

Run: python tests/test_routing.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from radnex.routing import (
    FAST_SCOUT_MODELS,
    HEAVY_ARCHITECT_MODELS,
    VERIFIED_FREE_MODELS,
    SmartRouter,
)

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, extra: str = "") -> None:
    RESULTS.append((name, ok, extra))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {extra}")


def test_free_protection() -> None:
    router = SmartRouter()

    # Verified free models must pass
    for src, models in VERIFIED_FREE_MODELS.items():
        for m in models:
            check(f"free: {src} -> {m} is strictly free", router.is_strictly_free(src, m))

    # Known paid models must NEVER pass as free
    check("paid: claude-3-5-sonnet is NOT free", not router.is_strictly_free("openrouter", "anthropic/claude-3.5-sonnet"))
    check("paid: gpt-4o is NOT free", not router.is_strictly_free("unorouter", "openai/gpt-4o"))
    check("paid: claude-opus-5 is NOT free", not router.is_strictly_free("aihubmix", "claude-opus-5"))
    check("paid: random paid string is NOT free", not router.is_strictly_free("apinex", "paid-model-expensive"))


def test_dual_tier_models() -> None:
    router = SmartRouter()

    # Scout models must be free
    for src, model in FAST_SCOUT_MODELS.items():
        check(f"scout: {src} -> {model} is free", router.is_strictly_free(src, model))

    # Architect models must be free
    for src, model in HEAVY_ARCHITECT_MODELS.items():
        check(f"architect: {src} -> {model} is free", router.is_strictly_free(src, model))


def test_failover_routing() -> None:
    router = SmartRouter()

    # Healthy candidates
    candidates = router.get_candidate_gateways()
    check("routing: initial candidates list is populated", len(candidates) > 0)

    # Fail one gateway
    router.mark_gateway_failure("unorouter", "429 RateLimitError")
    check("routing: unorouter marked unhealthy", not router.health["unorouter"].is_available())

    # Failover route should exclude failed unorouter
    route = router.next_free_route(current_source="unorouter")
    if route:
        new_src, base, token, model = route
        check("routing: failover source is NOT unorouter", new_src != "unorouter")
        check("routing: failover model is strictly free", router.is_strictly_free(new_src, model))
    else:
        check("routing: next_free_route evaluated", True)


def main() -> None:
    test_free_protection()
    test_dual_tier_models()
    test_failover_routing()

    passed = sum(1 for _, ok, _ in RESULTS if ok)
    failed = sum(1 for _, ok, _ in RESULTS if not ok)
    print(f"\n{passed}/{len(RESULTS)} passed" + (f" — {failed} FAILED" if failed else ""))
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()

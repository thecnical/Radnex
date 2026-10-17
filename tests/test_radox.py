"""Regression suite for the Radox AI source.

Run: python tests/test_radox.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from radnex import radox as rx_mod
from radnex import sources as s_mod

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, extra: str = "") -> None:
    RESULTS.append((name, ok, extra))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {extra}")


def test_host_recognition() -> None:
    check("host: matches bare host", rx_mod.is_radox("https://radoxai.com"))
    check("host: matches path", rx_mod.is_radox("https://radoxai.com/v1"))
    check("host: does not match openrouter", not rx_mod.is_radox("https://openrouter.ai"))
    check("host: does not match None", not rx_mod.is_radox(None))
    check("sources: active_key identifies radox", s_mod.active_key("https://radoxai.com") == "radox")
    check("sources: builtin contains radox", "radox" in s_mod.BUILTIN_KEYS)


def test_credentials_flow() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        prof = tmp / "source"
        with mock.patch.object(rx_mod, "PROFILE", prof):
            check("creds: none initially", rx_mod.load_credentials() is None)
            saved = rx_mod.save_key("sk-rx-testkey-12345678", "deepseek-v3")
            check("creds: written to profile", saved.is_file())
            creds = rx_mod.load_credentials()
            check("creds: load returns tuple", creds is not None and creds[0] == "sk-rx-testkey-12345678")
            check("creds: model saved", creds is not None and creds[1] == "deepseek-v3")


def test_models_fallback() -> None:
    with mock.patch.object(rx_mod, "CACHE_TTL", 0):
        models = [rx_mod.Model(id=m, label=m, tools=True, free=True) for m in rx_mod.PREFERRED_FREE_MODELS]
        rx_mod._CACHE[""] = (models, 9999999999.0)
        free, _ = rx_mod.free_models("")
        check("models: free_models returns list", isinstance(free, list) and len(free) > 0)
        usable, _ = rx_mod.usable_free_models("")
        check("models: usable_free_models returns chat models", all(m.chat for m in usable))


def main() -> None:
    test_host_recognition()
    test_credentials_flow()
    test_models_fallback()

    passed = sum(1 for _, ok, _ in RESULTS if ok)
    failed = sum(1 for _, ok, _ in RESULTS if not ok)
    print(f"\n{passed}/{len(RESULTS)} passed" + (f" — {failed} FAILED" if failed else ""))
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()

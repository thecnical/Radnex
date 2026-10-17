"""Regression suite for the APInex source.

Run: python tests/test_apinex.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from radnex import apinex as api_mod
from radnex import sources as s_mod

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, extra: str = "") -> None:
    RESULTS.append((name, ok, extra))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {extra}")


def test_host_recognition() -> None:
    check("host: matches bare host", api_mod.is_apinex("https://apinex.bond"))
    check("host: matches api subdomain", api_mod.is_apinex("https://api.apinex.bond"))
    check("host: matches /v1 path", api_mod.is_apinex("https://api.apinex.bond/v1"))
    check("host: does not match openrouter", not api_mod.is_apinex("https://openrouter.ai"))
    check("host: does not match None", not api_mod.is_apinex(None))
    check("sources: active_key identifies apinex", s_mod.active_key("https://api.apinex.bond") == "apinex")
    check("sources: builtin contains apinex", "apinex" in s_mod.BUILTIN_KEYS)


def test_credentials_flow() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        prof = tmp / "source"
        with mock.patch.object(api_mod, "PROFILE", prof):
            check("creds: none initially", api_mod.load_credentials() is None)
            saved = api_mod.save_key("sk-api-testkey-12345678", "deepseek-v4.1-flash")
            check("creds: written to profile", saved.is_file())
            creds = api_mod.load_credentials()
            check("creds: load returns tuple", creds is not None and creds[0] == "sk-api-testkey-12345678")
            check("creds: model saved", creds is not None and creds[1] == "deepseek-v4.1-flash")


def test_free_models_filtering() -> None:
    models, _ = api_mod.fetch_models("mock-token")
    check("models: fetch returns list", isinstance(models, list) and len(models) > 0)
    free, _ = api_mod.free_models("mock-token")
    check("models: free_models returns subset", isinstance(free, list) and len(free) > 0)
    usable, _ = api_mod.usable_free_models("mock-token")
    check("models: usable_free_models returns chat models", all(m.chat for m in usable))


def main() -> None:
    test_host_recognition()
    test_credentials_flow()
    test_free_models_filtering()

    passed = sum(1 for _, ok, _ in RESULTS if ok)
    failed = sum(1 for _, ok, _ in RESULTS if not ok)
    print(f"\n{passed}/{len(RESULTS)} passed" + (f" — {failed} FAILED" if failed else ""))
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()

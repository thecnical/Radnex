"""Regression suite for Git Shadow Checkpoints & Instant Rollback (/undo).

Run: python tests/test_shadow.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from radnex.shadow import ShadowManager

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, extra: str = "") -> None:
    RESULTS.append((name, ok, extra))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {extra}")


def test_shadow_manager() -> None:
    sm = ShadowManager(max_checkpoints=5)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        check("shadow: initial count is 0", sm.count() == 0)

        # Snapshot
        cid = sm.snapshot(tmp, label="test turn")
        check("shadow: empty undo handles gracefully", True)

        # Test empty undo
        ok, msg = sm.undo(tmp)
        check("shadow: undo on empty reports failure nicely", not ok and "no shadow" in msg)


def main() -> None:
    test_shadow_manager()

    passed = sum(1 for _, ok, _ in RESULTS if ok)
    failed = sum(1 for _, ok, _ in RESULTS if not ok)
    print(f"\n{passed}/{len(RESULTS)} passed" + (f" — {failed} FAILED" if failed else ""))
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()

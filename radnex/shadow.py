"""Git Shadow Checkpoints and Instant Rollback (/undo) for Radnex.

Automatically snapshots the workspace before mutating tool operations so any
unintended edits, file writes, or shell command effects can be reversed
instantly with `/undo`.
"""

from __future__ import annotations

import logging
import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("radnex.shadow")


@dataclass
class ShadowCheckpoint:
    id: str
    timestamp: float
    label: str
    stash_ref: str | None = None
    files_snapshot: dict[str, str | None] = field(default_factory=dict)


class ShadowManager:
    """Manages workspace checkpoints and rollbacks."""

    def __init__(self, max_checkpoints: int = 20) -> None:
        self.checkpoints: list[ShadowCheckpoint] = []
        self.max_checkpoints = max_checkpoints

    def _is_git_repo(self, workdir: Path) -> bool:
        return (workdir / ".git").exists()

    def snapshot(self, workdir: Path, label: str = "") -> str | None:
        """Create a lightweight shadow checkpoint of the workspace."""
        workdir = workdir.resolve()
        now = time.time()
        cid = f"cp_{int(now * 1000)}"

        if self._is_git_repo(workdir):
            try:
                # Use git stash create to create a dangling commit object without touching index/worktree
                proc = subprocess.run(
                    ["git", "stash", "create", f"Radnex shadow: {label or cid}"],
                    cwd=str(workdir),
                    capture_output=True,
                    text=True,
                    timeout=5.0,
                )
                stash_ref = proc.stdout.strip()
                if stash_ref:
                    cp = ShadowCheckpoint(
                        id=cid,
                        timestamp=now,
                        label=label or "pre-turn checkpoint",
                        stash_ref=stash_ref,
                    )
                    self._push_checkpoint(cp)
                    return cid
            except Exception as e:
                logger.debug("git stash create failed: %s", e)

        # Fallback: if not git or stash create returned empty (clean tree), record commit HEAD
        if self._is_git_repo(workdir):
            try:
                proc = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=str(workdir),
                    capture_output=True,
                    text=True,
                    timeout=2.0,
                )
                head_ref = proc.stdout.strip()
                if head_ref:
                    cp = ShadowCheckpoint(
                        id=cid,
                        timestamp=now,
                        label=label or "HEAD checkpoint",
                        stash_ref=head_ref,
                    )
                    self._push_checkpoint(cp)
                    return cid
            except Exception:
                pass

        return None

    def _push_checkpoint(self, cp: ShadowCheckpoint) -> None:
        self.checkpoints.append(cp)
        if len(self.checkpoints) > self.max_checkpoints:
            self.checkpoints.pop(0)

    def undo(self, workdir: Path) -> tuple[bool, str]:
        """Roll back the last checkpoint."""
        if not self.checkpoints:
            return False, "no shadow checkpoints available to undo"

        cp = self.checkpoints.pop()
        workdir = workdir.resolve()

        if cp.stash_ref and self._is_git_repo(workdir):
            try:
                # Reset working tree to the checkpoint state
                subprocess.run(
                    ["git", "checkout", "HEAD", "--", "."],
                    cwd=str(workdir),
                    capture_output=True,
                    text=True,
                    timeout=5.0,
                )
                # If it was a stash commit, apply it back
                if len(cp.stash_ref) == 40:
                    subprocess.run(
                        ["git", "stash", "apply", cp.stash_ref],
                        cwd=str(workdir),
                        capture_output=True,
                        text=True,
                        timeout=5.0,
                    )
                return True, f"rolled back to checkpoint '{cp.label}' ({cp.id})"
            except Exception as exc:
                return False, f"rollback failed: {exc}"

        return False, "unable to restore checkpoint"

    def count(self) -> int:
        return len(self.checkpoints)


# Global singleton
shadow = ShadowManager()

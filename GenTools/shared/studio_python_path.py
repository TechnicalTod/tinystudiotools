"""Ensure ``GenTools/shared`` is importable (canonical implementation).

DCC entry points (Maya ``genTools.studio_python_path``, Unreal equivalent) duplicate
the path discovery below because they must run *before* this package is on
``sys.path``. Keep the candidate list in sync when editing either copy.
"""

from __future__ import annotations

import os
import sys

_BOOTSTRAPPED = False


def _insert(path: str) -> bool:
    path = path.replace("\\", "/")
    if os.path.isdir(path) and path not in sys.path:
        sys.path.insert(0, path)
        return True
    return False


def _candidate_paths(repo_env: str | None = None) -> list[str]:
    """Return ordered paths that may contain this package (``GenTools/shared``)."""
    candidates: list[str] = []

    script_dir = (os.getenv("SCRIPT_DIR") or "").replace("\\", "/").rstrip("/")
    if script_dir:
        candidates.append(script_dir + "/GenTools/shared")

    if repo_env:
        repo = (os.getenv(repo_env) or "").replace("\\", "/").rstrip("/")
        if repo:
            tools_root = os.path.dirname(os.path.dirname(repo))
            candidates.append(tools_root + "/GenTools/shared")
            candidates.append(repo + "/shared")

    return candidates


def ensure_gen_tools_shared(repo_env: str | None = None) -> bool:
    """Insert ``GenTools/shared`` on ``sys.path``. Returns True if a path was added."""
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return True

    for path in _candidate_paths(repo_env):
        if _insert(path):
            _BOOTSTRAPPED = True
            return True

    _BOOTSTRAPPED = True
    return False

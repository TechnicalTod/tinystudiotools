"""Ensure TinyStudio shared Python packages are importable from Maya."""

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


def ensure_gen_tools_shared() -> bool:
    """Insert ``GenTools/shared`` on ``sys.path``. Returns True if a path was added."""
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return True

    candidates: list[str] = []

    script_dir = (os.getenv("SCRIPT_DIR") or "").replace("\\", "/").rstrip("/")
    if script_dir:
        candidates.append(script_dir + "/GenTools/shared")

    maya_repo = (os.getenv("MAYA_REPO") or "").replace("\\", "/").rstrip("/")
    if maya_repo:
        tools_root = os.path.dirname(os.path.dirname(maya_repo))
        candidates.append(tools_root + "/GenTools/shared")
        candidates.append(maya_repo + "/shared")

    this_dir = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(this_dir))))
    candidates.append(repo_root + "/GenTools/shared")

    for path in candidates:
        if _insert(path):
            _BOOTSTRAPPED = True
            return True

    _BOOTSTRAPPED = True
    return False

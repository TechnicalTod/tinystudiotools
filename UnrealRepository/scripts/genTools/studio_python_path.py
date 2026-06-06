"""Ensure TinyStudio shared Python packages are importable from Unreal."""

from __future__ import annotations

import os
import sys

_BOOTSTRAPPED = False
_SETDEC_BOOTSTRAPPED = False

_SETDEC_SRC = "SetDecSceneDescriptionIO/src"


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

    unreal_repo = (os.getenv("UNREAL_REPO") or "").replace("\\", "/").rstrip("/")
    if unreal_repo:
        tools_root = os.path.dirname(os.path.dirname(unreal_repo))
        candidates.append(tools_root + "/GenTools/shared")
        candidates.append(unreal_repo + "/shared")

    this_dir = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(this_dir)))
    candidates.append(repo_root + "/GenTools/shared")

    for path in candidates:
        if _insert(path):
            _BOOTSTRAPPED = True
            return True

    _BOOTSTRAPPED = True
    return False


def _setdec_src_candidates() -> list[str]:
    candidates: list[str] = []

    script_dir = (os.getenv("SCRIPT_DIR") or "").replace("\\", "/").rstrip("/")
    if script_dir:
        candidates.append(f"{script_dir}/GenTools/{_SETDEC_SRC}")

    lib_dir = (os.getenv("TINYSTUDIO_LIB_DIR") or "").replace("\\", "/").rstrip("/")
    if lib_dir:
        candidates.append(f"{lib_dir}/TinyStudioTools/GenTools/{_SETDEC_SRC}")

    unreal_repo = (os.getenv("UNREAL_REPO") or "").replace("\\", "/").rstrip("/")
    if unreal_repo:
        tools_root = os.path.dirname(os.path.dirname(unreal_repo))
        candidates.append(f"{tools_root}/GenTools/{_SETDEC_SRC}")

    this_dir = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(this_dir)))
    candidates.append(f"{repo_root}/GenTools/{_SETDEC_SRC}")

    return candidates


def ensure_setdec_scene_description_io() -> bool:
    """Insert ``setdec_scene_description_io`` on ``sys.path``. Returns True if added."""
    global _SETDEC_BOOTSTRAPPED
    if _SETDEC_BOOTSTRAPPED:
        return True

    for path in _setdec_src_candidates():
        if _insert(path):
            _SETDEC_BOOTSTRAPPED = True
            return True

    _SETDEC_BOOTSTRAPPED = True
    return False

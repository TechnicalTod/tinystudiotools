"""Shared TinyStudio paths (GenTools, stylesheets, etc.)."""

import os


def _normalize(path):
    return path.replace("\\", "/") if path else None


def tiny_studio_tools_root():
    """Resolve TinyStudioTools repo root from launcher or DCC env vars."""
    script_dir = _normalize(os.getenv("SCRIPT_DIR"))
    if script_dir:
        return script_dir.rstrip("/")

    maya_repo = _normalize(os.getenv("MAYA_REPO"))
    if maya_repo:
        # .../MayaRepository/2026 -> .../TinyStudioTools
        return os.path.dirname(os.path.dirname(maya_repo.rstrip("/")))

    unreal_repo = _normalize(os.getenv("UNREAL_REPO"))
    if unreal_repo:
        return os.path.dirname(unreal_repo.rstrip("/"))

    return None


_tools_root = tiny_studio_tools_root()
styleSheetFilepath = (
    "{}/GenTools/pyQtStyleSheets/".format(_tools_root) if _tools_root else None
)

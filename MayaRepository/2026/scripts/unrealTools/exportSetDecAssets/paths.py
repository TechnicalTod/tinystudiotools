"""Set Dec publish paths under the launcher show layout.

Published assets live at::

    {show_root}/assets/setdec/{group}/{asset}/{variant}/{version}/

where ``show_root`` is resolved from ``TINYSTUDIO_BASE_SHOW_DIR`` and
``SHOW_NAME`` (same rules as Asset Manager / Workfile Publisher).
"""

from __future__ import annotations

import os
from pathlib import Path

SETDEC_CATEGORY = "setdec"


def _env(name: str) -> str:
    return os.environ.get(name, "").strip()


def _normalize_base_and_show(base: str, show: str) -> Path:
    """Return the absolute show root path."""
    show = show.strip().strip("/\\")
    base_path = Path(base.replace("\\", "/"))

    if base_path.name == show and base_path.exists():
        return base_path

    show_root = base_path / show
    if show_root.exists():
        return show_root

    base_str = str(base_path).replace("\\", "/").rstrip("/")
    suffix = "/" + show
    if base_str.endswith(suffix) or base_str.endswith(show):
        trimmed = base_str[: -len(show)].rstrip("/\\")
        if trimmed:
            candidate = Path(trimmed) / show
            if candidate.exists():
                return candidate

    return show_root


def show_root_for(show: str) -> Path:
    """Resolve ``S:/<SHOW_NAME>`` (or normalized equivalent) from launcher env."""
    base = _env("TINYSTUDIO_BASE_SHOW_DIR")
    if not base:
        raise RuntimeError(
            "TINYSTUDIO_BASE_SHOW_DIR is not set. Launch Maya through TinyStudioLauncher."
        )
    if not show:
        show = _env("SHOW_NAME")
    if not show:
        raise RuntimeError(
            "SHOW_NAME is not set. Launch Maya through TinyStudioLauncher."
        )
    return _normalize_base_and_show(base, show)


def _setdec_root(show: str) -> Path:
    return show_root_for(show) / "assets" / SETDEC_CATEGORY


def _to_maya_path(path: Path) -> str:
    return path.as_posix()


def setdec_production_folder(show):
    """Root folder containing all Set Dec groups for a show."""
    return _to_maya_path(_setdec_root(show))


def setdec_group_folder(show, group_name):
    """Folder for one Set Dec group (contains per-asset subfolders)."""
    return _to_maya_path(_setdec_root(show) / group_name) + "/"


def version_asset_root(show, group_name, asset_short_name, variant_name, version_name):
    return (
        setdec_group_folder(show, group_name)
        + asset_short_name
        + "/"
        + variant_name
        + "/"
        + version_name
        + "/"
    )

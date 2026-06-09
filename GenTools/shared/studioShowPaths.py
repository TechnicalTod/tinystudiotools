"""Shared show-drive path helpers (Set Dec, assets root, etc.)."""

from __future__ import annotations

import os
from pathlib import Path

SETDEC_CATEGORY = "setdec"
_DRIVE_RELATIVE_PREFIX_LEN = 2  # "S:"


def normalize_disk_path(path: str) -> str:
    """Ensure ``S:folder/...`` becomes ``S:/folder/...`` for Unreal and ``os.path``."""
    if not path:
        return path
    path = path.replace("\\", "/")
    if (
        len(path) >= _DRIVE_RELATIVE_PREFIX_LEN
        and path[1] == ":"
        and (len(path) == _DRIVE_RELATIVE_PREFIX_LEN or path[_DRIVE_RELATIVE_PREFIX_LEN] not in "/\\")
    ):
        path = path[:_DRIVE_RELATIVE_PREFIX_LEN] + "/" + path[_DRIVE_RELATIVE_PREFIX_LEN:]
    return path


def _env(name: str) -> str:
    return os.environ.get(name, "").strip()


def normalize_show_root(base: str, show: str) -> Path:
    """Return absolute show root, folding duplicate show segments when needed."""
    show = show.strip().strip("/\\")
    base_path = Path(normalize_disk_path(base))

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


def show_root_for(show: str = "") -> Path:
    """Resolve ``{base}/{SHOW_NAME}`` from launcher environment variables."""
    base = _env("TINYSTUDIO_BASE_SHOW_DIR")
    if not base:
        raise RuntimeError(
            "TINYSTUDIO_BASE_SHOW_DIR is not set. Launch through TinyStudioLauncher."
        )
    if not show:
        show = _env("SHOW_NAME")
    if not show:
        raise RuntimeError(
            "SHOW_NAME is not set. Launch through TinyStudioLauncher."
        )
    return normalize_show_root(base, show)


def setdec_root(show: str = "") -> Path:
    return show_root_for(show) / "assets" / SETDEC_CATEGORY


def setdec_production_folder(show: str = "") -> str:
    """``{show_root}/assets/setdec`` — root of all Set Dec groups."""
    return setdec_root(show).as_posix()


def setdec_group_folder(show: str, group_name: str, *, trailing_slash: bool = False) -> str:
    """Folder for one Set Dec group (contains per-asset subfolders)."""
    path = (setdec_root(show) / group_name).as_posix()
    return path + "/" if trailing_slash else path


def version_asset_root(
    show: str,
    group_name: str,
    asset_short_name: str,
    variant_name: str,
    version_name: str,
) -> str:
    return (
        setdec_group_folder(show, group_name, trailing_slash=True)
        + asset_short_name
        + "/"
        + variant_name
        + "/"
        + version_name
        + "/"
    )


def list_setdec_groups(show: str = "") -> list[str]:
    root = setdec_production_folder(show)
    if not os.path.isdir(root):
        return []
    return sorted(
        name for name in os.listdir(root) if os.path.isdir(os.path.join(root, name))
    )


def is_setdec_asset_folder(setdec_root_path: str, path: str) -> bool:
    """True when ``path`` is ``…/setdec/{group}/{asset}``."""
    setdec_root_path = os.path.normpath(setdec_root_path).replace("\\", "/")
    path = os.path.normpath(path).replace("\\", "/")
    if not path.startswith(setdec_root_path):
        return False
    rel = path[len(setdec_root_path) :].strip("/")
    parts = [part for part in rel.split("/") if part]
    return len(parts) == 2 and os.path.isdir(path)

"""Set Dec publish paths — re-exports from GenTools/shared/studioShowPaths."""

from __future__ import annotations

from genTools.studio_python_path import ensure_gen_tools_shared

ensure_gen_tools_shared()

from studioShowPaths import (  # noqa: E402
    setdec_group_folder as _setdec_group_folder,
    setdec_production_folder,
    version_asset_root,
)

__all__ = ["setdec_production_folder", "setdec_group_folder", "version_asset_root"]


def setdec_group_folder(show, group_name):
    """Maya publish code expects a trailing slash on group folders."""
    return _setdec_group_folder(show, group_name, trailing_slash=True)

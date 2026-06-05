"""Set Dec folder paths — re-exports from GenTools/shared/studioShowPaths."""

from __future__ import annotations

from genTools.studio_python_path import ensure_gen_tools_shared

ensure_gen_tools_shared()

from studioShowPaths import (  # noqa: E402
    is_setdec_asset_folder,
    list_setdec_groups,
    setdec_group_folder,
    setdec_production_folder,
    show_root_for,
)

__all__ = [
    "show_root_for",
    "setdec_production_folder",
    "setdec_group_folder",
    "list_setdec_groups",
    "is_setdec_asset_folder",
]

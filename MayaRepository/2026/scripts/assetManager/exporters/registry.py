"""Export-step registry.

To add an export step:

1. Drop a module in ``exporters/plugins/`` exposing one function
   ``def run(ctx: ExportContext) -> ExportResult``.
2. Register it below in ``DEFAULT_EXPORTS`` (one line).
3. Reference its id under either ``default_exports`` (runs for every
   publish) or ``publish_types.<key>.exports`` in
   ``configs/asset_publish_schema.json``.

To remove a step, delete its JSON entry; the plugin file can stay.
"""

from __future__ import annotations

from typing import Callable, Dict, Optional

from .base import ExportContext, ExportResult
from .plugins import (
    copy_applied_textures,
    fbx_rig,
    fbx_selection,
    layout_placeholder,
    maya_scene,
)


ExportFn = Callable[[ExportContext], ExportResult]


DEFAULT_EXPORTS: Dict[str, ExportFn] = {
    "maya_scene": maya_scene.run,
    "copy_applied_textures": copy_applied_textures.run,
    "fbx_selection": fbx_selection.run,
    "fbx_rig": fbx_rig.run,
    "layout_placeholder": layout_placeholder.run,
}


def get_export(export_id: str) -> Optional[ExportFn]:
    return DEFAULT_EXPORTS.get(export_id)

"""Universal export: save the current scene next to the publish artifacts.

Runs for every publish type via ``default_exports``.

Params:
    extension (str, default ``".ma"``):
        File extension used when naming the scene file. ``".mb"`` will save
        a binary scene.
"""

from __future__ import annotations

from ..base import ExportContext, ExportResult


def run(ctx: ExportContext) -> ExportResult:
    extension = str(ctx.params.get("extension", ".ma"))
    if not extension.startswith("."):
        extension = "." + extension

    padding = ctx.schema.version_padding
    file_name = (
        f"{ctx.target.asset}_{ctx.target.publish_type}_{ctx.target.variant}"
        f"_v{ctx.version:0{padding}d}{extension}"
    )
    out = ctx.version_dir / file_name
    ctx.host.save_scene_as(out)
    return ExportResult(artifacts=[out.name])

"""Export current Maya selection to FBX (model publish)."""

from __future__ import annotations

from ..base import ExportContext, ExportResult


def run(ctx: ExportContext) -> ExportResult:
    padding = ctx.schema.version_padding
    file_name = (
        f"{ctx.target.asset}_{ctx.target.publish_type}_{ctx.target.variant}"
        f"_v{ctx.version:0{padding}d}.fbx"
    )
    out = ctx.version_dir / file_name
    ctx.host.export_fbx_selection(out)
    return ExportResult(artifacts=[out.name])

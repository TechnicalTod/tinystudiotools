"""Export the rig hierarchy plus an Unreal-ready FBX bundle."""

from __future__ import annotations

from ..base import ExportContext, ExportResult


def run(ctx: ExportContext) -> ExportResult:
    ctx.host.export_fbx_rig(ctx.version_dir, ctx.target.asset)
    return ExportResult(artifacts=["UnrealExport/"])

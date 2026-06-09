"""Model publish: Set Dec-compatible static mesh bundle (fbx/usd/maya/tex)."""

from __future__ import annotations

from ...core.paths import version_dir_name
from ..base import ExportContext, ExportError, ExportResult


def run(ctx: ExportContext) -> ExportResult:
    if not ctx.host.selection_is_single_mesh_transform():
        raise ExportError("Select exactly one mesh transform to publish.")

    padding = ctx.schema.version_padding
    version_label = f"v{ctx.version:0{padding}d}"
    file_stem = version_dir_name(
        ctx.target.asset,
        ctx.target.publish_type,
        ctx.target.variant,
        ctx.version,
        padding=padding,
    )
    base_path = ctx.version_dir.parent.as_posix()
    if not base_path.endswith("/"):
        base_path += "/"

    try:
        artifacts = ctx.host.publish_static_mesh_bundle(
            ctx.version_dir,
            file_stem=file_stem,
            asset_name=ctx.target.asset,
            variant_name=ctx.target.variant,
            version_label=version_label,
            base_path=base_path,
            publish_layout="asset_manager_model",
        )
    except RuntimeError as exc:
        raise ExportError(str(exc)) from exc

    return ExportResult(artifacts=artifacts)

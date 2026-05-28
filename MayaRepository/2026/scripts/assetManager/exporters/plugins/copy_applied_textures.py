"""Universal export: copy textures referenced by applied materials.

Walks the scene's shading network via the host and copies every referenced
texture into ``<version_dir>/<output_dir>/``. UDIM siblings are expanded by
the host so the bundle is complete.

Params:
    output_dir (str, default ``"tex"``):
        Sub-folder created under the version directory.
"""

from __future__ import annotations

import shutil

from ..base import ExportContext, ExportResult


def run(ctx: ExportContext) -> ExportResult:
    output_dir = str(ctx.params.get("output_dir", "tex"))
    dest_dir = ctx.version_dir / output_dir

    textures = ctx.host.collect_applied_textures()
    if not textures:
        return ExportResult(artifacts=[])

    dest_dir.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for src in textures:
        target = dest_dir / src.name
        try:
            shutil.copy2(src, target)
        except OSError:
            continue
        copied.append(f"{output_dir}/{target.name}")
    return ExportResult(artifacts=copied)

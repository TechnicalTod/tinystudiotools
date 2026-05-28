"""Layout publish placeholder.

Writes a small ``layout.json`` describing the publish intent. Full layout
export (per-asset references, USD, etc.) is a follow-up.
"""

from __future__ import annotations

import json

from ..base import ExportContext, ExportResult


def run(ctx: ExportContext) -> ExportResult:
    file_name = "layout.json"
    note = (
        "Layout publish stub. Env assets may later export USD/scene description "
        "under publish/unreal; chr/prop use manifest-only in v1."
    )
    if ctx.target.category.lower() == "env":
        note += " Target category is env — wire USD export in a follow-up."

    out = ctx.version_dir / file_name
    out.write_text(
        json.dumps(
            {
                "asset": ctx.target.asset,
                "category": ctx.target.category,
                "publish_type": ctx.target.publish_type,
                "variant": ctx.target.variant,
                "version": ctx.version,
                "note": note,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return ExportResult(artifacts=[file_name])

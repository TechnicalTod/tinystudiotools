"""Dispatch exports for a publish.

``run_exports`` walks the schema's universal ``default_exports`` first, then
the publish-type's ``exports`` array. Each entry resolves through the export
registry to a single handler; adding a new export means adding one plugin
module + one line in :mod:`assetManager.exporters.registry`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

from ..core.schema import AssetPublishSchema, ExportStepSpec
from ..core.target import AssetPublishTarget
from ..host import MayaHost


class ExportError(RuntimeError):
    pass


@dataclass(frozen=True)
class ExportContext:
    """Everything an export plugin needs to write its artifact(s)."""

    host: MayaHost
    schema: AssetPublishSchema
    target: AssetPublishTarget
    version_dir: Path
    version: int
    spec: ExportStepSpec

    @property
    def params(self) -> Dict[str, Any]:
        return self.spec.params


@dataclass
class ExportResult:
    """Artifacts produced by a single export step."""

    artifacts: List[str] = field(default_factory=list)


def run_exports(
    host: MayaHost,
    schema: AssetPublishSchema,
    target: AssetPublishTarget,
    version_dir: Path,
    version: int,
) -> list[str]:
    """Run the universal defaults then the per-type exports."""
    from .registry import get_export  # local import to break import cycles

    type_spec = schema.get_publish_type(target.publish_type)
    steps: list[ExportStepSpec] = list(schema.default_exports) + list(type_spec.exports)

    artifacts: list[str] = []
    for step in steps:
        handler = get_export(step.id)
        if handler is None:
            raise ExportError(
                f"Unknown export id {step.id!r} — register it in "
                "exporters/registry.py."
            )
        ctx = ExportContext(
            host=host,
            schema=schema,
            target=target,
            version_dir=version_dir,
            version=version,
            spec=step,
        )
        result = handler(ctx)
        artifacts.extend(result.artifacts)
    return artifacts

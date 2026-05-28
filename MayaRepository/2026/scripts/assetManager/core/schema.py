"""Load asset_publish_schema.json.

The schema is the **only** place new pre-publish checks or export steps need
to be configured once their Python handlers are registered:

* ``publish_types.<key>.checks`` is a list of check ids. Each entry may be
  ``{ "id": "asset_name_pascal_case", "severity": "warning",
       "params": { "allow_lowercase_segments": true } }``.
  ``nodes`` is honored as a top-level convenience for legacy checks.
* ``publish_types.<key>.exports`` is an ordered list of export-step ids. Each
  entry may be either ``"fbx_selection"`` or
  ``{ "id": "fbx_selection", "params": { ... } }``.
* ``default_exports`` (optional, top-level) is an ordered list run for every
  publish *before* per-type exports — used for the universal Maya scene +
  applied textures bundle.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List


SCHEMA_FILENAME = "asset_publish_schema.json"


class SchemaError(RuntimeError):
    pass


@dataclass(frozen=True)
class CheckSpec:
    id: str
    severity: str
    params: Dict[str, Any] = field(default_factory=dict)

    # Backwards-compat accessor: many older configs used a top-level ``nodes``
    # list with the legacy ``nodes_exist`` check. The loader copies that into
    # ``params["nodes"]`` so plugins only have one place to look.
    @property
    def nodes(self) -> List[str]:
        value = self.params.get("nodes", [])
        return list(value) if isinstance(value, (list, tuple)) else []


@dataclass(frozen=True)
class ExportStepSpec:
    id: str
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PublishTypeSpec:
    key: str
    label: str
    checks: List[CheckSpec]
    exports: List[ExportStepSpec]


@dataclass(frozen=True)
class AssetPublishSchema:
    allowed_categories: List[str]
    default_variant: str
    version_padding: int
    dcc: str
    publish_types: Dict[str, PublishTypeSpec]
    default_exports: List[ExportStepSpec] = field(default_factory=list)

    def get_publish_type(self, key: str) -> PublishTypeSpec:
        if key not in self.publish_types:
            raise SchemaError(f"Unknown publish type {key!r}.")
        return self.publish_types[key]

    def publish_type_keys(self) -> List[str]:
        return list(self.publish_types.keys())


def default_schema_path() -> Path:
    return Path(__file__).resolve().parents[1] / "configs" / SCHEMA_FILENAME


# ---------------------------------------------------------------- entry parsing

_CHECK_RESERVED_KEYS = {"id", "severity", "params"}


def _parse_check_entry(raw: Any) -> CheckSpec:
    """Accept either ``"check_id"`` or ``{id, severity, params, ...}``.

    Any keys besides ``id`` / ``severity`` / ``params`` (e.g. legacy ``nodes``)
    are folded into ``params`` so handlers only read one dict.
    """
    if isinstance(raw, str):
        return CheckSpec(id=raw, severity="error")

    if not isinstance(raw, dict):
        raise SchemaError(f"Check entry must be a string or object, got {raw!r}.")

    if "id" not in raw:
        raise SchemaError(f"Check entry missing 'id': {raw!r}.")

    params: Dict[str, Any] = {}
    explicit = raw.get("params") or {}
    if not isinstance(explicit, dict):
        raise SchemaError(f"Check 'params' must be an object: {raw!r}.")
    params.update(explicit)
    for key, value in raw.items():
        if key in _CHECK_RESERVED_KEYS:
            continue
        params.setdefault(key, value)

    return CheckSpec(
        id=str(raw["id"]),
        severity=str(raw.get("severity", "error")),
        params=params,
    )


def _parse_export_entry(raw: Any) -> ExportStepSpec:
    if isinstance(raw, str):
        return ExportStepSpec(id=raw)
    if not isinstance(raw, dict):
        raise SchemaError(f"Export entry must be a string or object, got {raw!r}.")
    if "id" not in raw:
        raise SchemaError(f"Export entry missing 'id': {raw!r}.")
    params = raw.get("params") or {}
    if not isinstance(params, dict):
        raise SchemaError(f"Export 'params' must be an object: {raw!r}.")
    return ExportStepSpec(id=str(raw["id"]), params=dict(params))


def load_schema(path: Path | None = None) -> AssetPublishSchema:
    schema_path = path or default_schema_path()
    if not schema_path.is_file():
        raise SchemaError(f"Schema not found: {schema_path}")
    raw: Dict[str, Any] = json.loads(schema_path.read_text(encoding="utf-8"))

    publish_types: Dict[str, PublishTypeSpec] = {}
    for key, spec in raw.get("publish_types", {}).items():
        checks = [_parse_check_entry(c) for c in spec.get("checks", [])]
        exports = [_parse_export_entry(e) for e in spec.get("exports", [])]
        publish_types[key] = PublishTypeSpec(
            key=key,
            label=spec.get("label", key.title()),
            checks=checks,
            exports=exports,
        )

    default_exports = [
        _parse_export_entry(e) for e in raw.get("default_exports", [])
    ]

    return AssetPublishSchema(
        allowed_categories=list(raw.get("allowed_categories", [])),
        default_variant=str(raw.get("default_variant", "main")),
        version_padding=int(raw.get("version_padding", 3)),
        dcc=str(raw.get("dcc", "maya")),
        publish_types=publish_types,
        default_exports=default_exports,
    )

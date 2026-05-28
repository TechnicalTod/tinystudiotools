"""Pure path-building functions and the JSON-backed schema loader.

The schema describes:

* Which DCCs exist, their file extension, and which contexts (asset / shot)
  they support.
* The on-disk folder layout for ``work/`` and ``publish/`` paths.
* The default task list per DCC + context combo.
* The default variant (``main``) and zero-padded version width.

Everything here is host-agnostic and side-effect free apart from reading the
schema JSON.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .context import StudioContext


SCHEMA_FILENAME = "path_schema.json"

# Variant names must be filesystem-safe slugs. Spaces are normalised to
# underscores; anything outside this allow-list is rejected.
_VARIANT_ALLOWED = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


class SchemaError(RuntimeError):
    """Raised when the path schema config is missing / malformed."""


@dataclass(frozen=True)
class DCCSpec:
    """A single DCC's schema entry."""

    key: str
    label: str
    extension: str
    supports_asset: bool
    supports_shot: bool
    asset_tasks: List[str] = field(default_factory=list)
    shot_tasks: List[str] = field(default_factory=list)

    def tasks_for(self, kind: str) -> List[str]:
        """Return the task list for ``"asset"`` or ``"shot"``."""
        if kind == "asset":
            return list(self.asset_tasks)
        if kind == "shot":
            return list(self.shot_tasks)
        raise ValueError(f"Unknown context kind {kind!r}")

    def supports(self, kind: str) -> bool:
        if kind == "asset":
            return self.supports_asset
        if kind == "shot":
            return self.supports_shot
        raise ValueError(f"Unknown context kind {kind!r}")


@dataclass(frozen=True)
class PathSchema:
    """In-memory representation of ``configs/path_schema.json``."""

    default_variant: str
    version_padding: int
    asset_filename: str
    shot_filename: str
    dccs: Dict[str, DCCSpec]

    def get_dcc(self, key: str) -> DCCSpec:
        if key not in self.dccs:
            raise SchemaError(f"Unknown DCC {key!r}; expected one of {list(self.dccs)}.")
        return self.dccs[key]


def load_schema(config_path: Path) -> PathSchema:
    """Load ``path_schema.json`` from disk.

    Args:
        config_path: Path to ``configs/path_schema.json``.

    Raises:
        SchemaError: If the file is missing or malformed.
    """
    if not config_path.exists():
        raise SchemaError(f"Path schema not found: {config_path}")

    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SchemaError(f"Invalid JSON in {config_path}: {exc}") from exc

    asset_block = raw.get("asset") or {}
    shot_block = raw.get("shot") or {}
    dcc_block = raw.get("dcc") or {}
    if not dcc_block:
        raise SchemaError(f"No 'dcc' block in {config_path}")

    dccs: Dict[str, DCCSpec] = {}
    for key, entry in dcc_block.items():
        dccs[key] = DCCSpec(
            key=key,
            label=entry.get("label", key),
            extension=entry["extension"],
            supports_asset=bool(entry.get("supports_asset", False)),
            supports_shot=bool(entry.get("supports_shot", False)),
            asset_tasks=list(entry.get("asset_tasks", [])),
            shot_tasks=list(entry.get("shot_tasks", [])),
        )

    return PathSchema(
        default_variant=str(raw.get("default_variant", "main")),
        version_padding=int(raw.get("version_padding", 3)),
        asset_filename=str(asset_block.get("filename", "{asset}_{task}_{variant}_v{version:03d}.{ext}")),
        shot_filename=str(shot_block.get("filename", "{shot}_{task}_{variant}_v{version:03d}.{ext}")),
        dccs=dccs,
    )


def default_schema_path() -> Path:
    """Resolve the bundled schema path next to the publisher source tree."""
    here = Path(__file__).resolve()
    # core/path_schema.py -> core/ -> workfile_publisher/ -> src/ -> repo root.
    repo_root = here.parents[3]
    return repo_root / "configs" / SCHEMA_FILENAME


def normalize_variant(value: Optional[str], schema: PathSchema) -> str:
    """Normalise and validate a user-supplied variant name.

    * ``None`` or empty -> default variant from the schema (``"main"``).
    * Whitespace stripped; spaces converted to underscores; lowercased.
    * Must match ``[a-z0-9][a-z0-9_-]*`` once normalised.

    Raises:
        ValueError: If the cleaned value is empty or contains illegal chars.
    """
    if value is None or not value.strip():
        return schema.default_variant

    cleaned = value.strip().lower().replace(" ", "_")
    if not _VARIANT_ALLOWED.match(cleaned):
        raise ValueError(
            f"Variant {value!r} is not valid; use lowercase letters, digits, "
            "underscore or dash, starting with a letter or digit."
        )
    return cleaned


# ---------------------------------------------------------------------------
# Path builders


def asset_workfile_dir(
    ctx: StudioContext,
    category: str,
    asset: str,
    dcc: str,
    task: str,
) -> Path:
    """Build the work directory for an asset/dcc/task combo.

    ``S:/<show>/assets/<category>/<asset>/work/<dcc>/<task>/``
    """
    return ctx.assets_root / category / asset / "work" / dcc / task


def shot_workfile_dir(
    ctx: StudioContext,
    episode: str,
    sequence: str,
    shot: str,
    dcc: str,
    task: str,
) -> Path:
    """Build the work directory for an episode/sequence/shot combo.

    ``S:/<show>/episodes/<episode>/<sequence>/<shot>/work/<dcc>/<task>/``
    """
    return ctx.episodes_root / episode / sequence / shot / "work" / dcc / task


def build_asset_filename(
    asset: str,
    task: str,
    variant: str,
    version: int,
    ext: str,
    *,
    padding: int = 3,
) -> str:
    """Render ``<asset>_<task>_<variant>_v###.<ext>``."""
    return f"{asset}_{task}_{variant}_v{version:0{padding}d}.{ext}"


def build_shot_filename(
    shot: str,
    task: str,
    variant: str,
    version: int,
    ext: str,
    *,
    padding: int = 3,
) -> str:
    """Render ``<shot>_<task>_<variant>_v###.<ext>``."""
    return f"{shot}_{task}_{variant}_v{version:0{padding}d}.{ext}"

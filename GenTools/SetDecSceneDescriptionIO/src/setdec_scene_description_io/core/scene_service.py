"""Import / export orchestration for scene descriptions."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from .context import StudioContext
from .paths import ScenePaths, SceneSchema, load_scene_schema
from .usd_io import parse_usd, write_usd
from .versioning import (
    SceneDescriptionEntry,
    list_scene_descriptions,
    next_version,
    normalize_env_name,
    normalize_variant,
)

if TYPE_CHECKING:
    from ..adapters.base import SceneAdapter


@dataclass(frozen=True)
class SceneTarget:
    """An env + variant the UI is operating on."""

    env: str
    variant: str


class SceneDescriptionService:
    """List, export, and import scene descriptions for one show."""

    def __init__(
        self,
        context: StudioContext,
        adapter: "SceneAdapter",
        schema: Optional[SceneSchema] = None,
    ) -> None:
        self._context = context
        self._adapter = adapter
        self._schema = schema or load_scene_schema()
        self._paths = ScenePaths(str(context.base_show_dir), self._schema)

    @property
    def schema(self) -> SceneSchema:
        return self._schema

    @property
    def paths(self) -> ScenePaths:
        return self._paths

    def list_for_target(self, target: SceneTarget) -> List[SceneDescriptionEntry]:
        return list_scene_descriptions(
            self._paths,
            self._context.show,
            target.env,
            target.variant,
        )

    def next_version_label(self, target: SceneTarget) -> str:
        entries = self.list_for_target(target)
        return next_version(entries, padding=self._schema.version_padding)

    def build_target(
        self,
        env_raw: str,
        variant_raw: str,
        *,
        warn: bool = False,
    ) -> Optional[SceneTarget]:
        try:
            env = normalize_env_name(env_raw)
            variant = normalize_variant(variant_raw, self._schema)
        except ValueError:
            if warn:
                return None
            return None
        return SceneTarget(env=env, variant=variant)

    def export_scene(self, target: SceneTarget) -> Optional[Path]:
        """Gather the live scene and write the next versioned ``.usda``."""
        version_label = self.next_version_label(target)
        version_folder = self._paths.version_folder(
            self._context.show, target.env, target.variant, version_label
        )
        os.makedirs(version_folder, exist_ok=True)
        usd_path = self._paths.scene_description_file(
            self._context.show, target.env, target.variant, version_label
        )
        written = write_usd(usd_path, self._adapter.gather())
        return Path(written) if written else None

    def import_scene(self, entry: SceneDescriptionEntry) -> None:
        """Rebuild the scene from a published scene description."""
        self._adapter.apply(parse_usd(str(entry.path)))

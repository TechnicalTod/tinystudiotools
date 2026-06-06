"""Scene-description version scanning on disk."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List

from .paths import ScenePaths, SceneSchema

_VERSION_DIR_RE = re.compile(r"^v(\d+)$", re.IGNORECASE)


@dataclass(frozen=True)
class SceneDescriptionEntry:
    """One published scene-description ``.usda`` on disk."""

    path: Path
    env: str
    variant: str
    version: int
    filename: str
    modified: str

    @property
    def version_label(self) -> str:
        return f"v{self.version:03d}"


def list_scene_descriptions(
    paths: ScenePaths,
    show: str,
    env: str,
    variant: str,
) -> List[SceneDescriptionEntry]:
    """Return scene descriptions for one env/variant, newest version first."""
    variant_dir = paths.variant_folder(show, env, variant)
    entries: List[SceneDescriptionEntry] = []

    for version_name in ScenePaths.list_subdirs(variant_dir):
        match = _VERSION_DIR_RE.match(version_name)
        if not match:
            continue
        version_num = int(match.group(1))
        file_path = Path(paths.scene_description_file(show, env, variant, version_name))
        if not file_path.is_file():
            continue
        try:
            mtime = file_path.stat().st_mtime
            modified = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        except OSError:
            modified = ""
        entries.append(
            SceneDescriptionEntry(
                path=file_path,
                env=env,
                variant=variant,
                version=version_num,
                filename=file_path.name,
                modified=modified,
            )
        )

    entries.sort(key=lambda entry: entry.version, reverse=True)
    return entries


def next_version(
    entries: List[SceneDescriptionEntry],
    *,
    padding: int = 3,
) -> str:
    """Return the next version folder label (e.g. ``v003``)."""
    if not entries:
        return f"v{1:0{padding}d}"
    return f"v{max(entry.version for entry in entries) + 1:0{padding}d}"


def normalize_env_name(value: str) -> str:
    cleaned = value.strip().replace(" ", "_")
    if not cleaned:
        raise ValueError("Environment name is required.")
    return cleaned


def normalize_variant(value: str, schema: SceneSchema) -> str:
    if not value.strip():
        return schema.default_variant
    return value.strip().lower().replace(" ", "_")

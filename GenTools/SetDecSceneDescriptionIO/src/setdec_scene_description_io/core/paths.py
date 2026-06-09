"""Path building for SetDec scene descriptions.

Two concerns live here, both host-agnostic and free of numpy / DCC imports:

* :func:`complete_path` / :func:`transform_path` - build the path to a single
  *published asset* (``.usda`` reference, ``.ma`` file, or Unreal ``/Game`` asset).
* :class:`ScenePaths` - build the on-disk path of the *scene description* file
  itself, driven by ``configs/setdec_scene_paths.json``.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


SCHEMA_FILENAME = "setdec_scene_paths.json"


def _publish_bundle_paths():
    try:
        from publish_bundle_paths import (  # type: ignore[import-not-found]
            complete_path as _complete_path,
            disk_asset_folder as _disk_asset_folder,
            parse_ue_setdec_static_mesh_object_path as _parse_setdec,
            parse_ue_asset_manager_static_mesh_object_path as _parse_asset_manager,
            parse_ue_static_mesh_object_path,
        )
        return (
            _complete_path,
            _disk_asset_folder,
            _parse_setdec,
            _parse_asset_manager,
            parse_ue_static_mesh_object_path,
        )
    except ImportError:
        return None


def complete_path(file_path, variant, version, asset_name, ext):
    """Build the path to a published asset in the requested flavour."""
    loaded = _publish_bundle_paths()
    if loaded is not None:
        _complete_path, _, _, _, _ = loaded
        return _complete_path(file_path, variant, version, asset_name, ext)

    if ext == "maya":
        path_ext = ".ma"
    elif ext == "usd":
        path_ext = ".usda"
    else:
        path_ext = "." + ext

    if ext == "ue":
        file_path = _to_ue_publish_root(file_path)
        if not file_path.endswith("/"):
            file_path += "/"
        final_path = (
            f"{file_path}{asset_name}/{variant}/{version}/{asset_name}_{version}"
        )
    else:
        file_path = file_path.replace("\\", "/")
        final_path = (
            file_path
            + asset_name
            + "/"
            + variant
            + "/"
            + version
            + "/"
            + ext
            + "/"
            + asset_name
            + "_"
            + version
            + path_ext
        )

    return final_path.strip()


def disk_asset_folder(base_path: str, asset_name: str) -> str:
    loaded = _publish_bundle_paths()
    if loaded is not None:
        _, _disk_asset_folder, _, _, _ = loaded
        return _disk_asset_folder(base_path, asset_name)
    normalized = base_path.replace("\\", "/").rstrip("/")
    return f"{normalized}/{asset_name}"


@dataclass(frozen=True)
class SetDecUeMeshIdentity:
    """Parsed Set Dec identity from an Unreal static-mesh object path."""

    group_name: str
    asset_name: str
    variant: str
    version: str


def parse_ue_setdec_static_mesh_object_path(ue_path: str) -> Optional[SetDecUeMeshIdentity]:
    """Parse ``/Game/01_Assets/SETDEC/{group}/{asset}/{variant}/{version}/…``."""
    loaded = _publish_bundle_paths()
    if loaded is not None:
        _, _, _parse_setdec, _, parse_ue_static_mesh_object_path = loaded
        identity = parse_ue_static_mesh_object_path(ue_path)
        if identity is None or identity.layout != "setdec":
            return None
        return SetDecUeMeshIdentity(
            group_name=identity.base_path.rstrip("/").split("/")[-1],
            asset_name=identity.asset_name,
            variant=identity.variant,
            version=identity.version,
        )

    path = ue_path.split(".")[0].replace("\\", "/")
    marker = "/setdec/"
    idx = path.lower().find(marker)
    if idx == -1:
        return None

    parts = [part for part in path[idx + len(marker) :].split("/") if part]
    if len(parts) < 5:
        return None

    group_name, asset_name, variant, version, mesh_name = parts[:5]
    expected_mesh_name = f"{asset_name}_{version}"
    if mesh_name != expected_mesh_name:
        return None

    return SetDecUeMeshIdentity(
        group_name=group_name,
        asset_name=asset_name,
        variant=variant,
        version=version,
    )


def setdec_group_base_path(show_root: str, group_name: str) -> str:
    """Show-drive Set Dec group folder from a resolved show root."""
    normalized = show_root.replace("\\", "/").rstrip("/")
    return f"{normalized}/assets/setdec/{group_name}/"


def transform_path(original_path, pivot, new_base):
    """Re-root ``original_path`` from ``pivot`` onto ``new_base``.

    e.g. ``.../SETDEC/foo`` with pivot ``SETDEC`` and base ``/Game/01_Assets/``
    becomes ``/Game/01_Assets/SETDEC/foo``. Returns the input unchanged if the
    pivot is not present.
    """
    pivot_index = original_path.find(pivot)
    if pivot_index == -1:
        return original_path
    return new_base + original_path[pivot_index:]


def _to_ue_publish_root(file_path: str) -> str:
    """Map a show-drive publish folder to the Unreal content root."""
    loaded = _publish_bundle_paths()
    if loaded is not None:
        try:
            from publish_bundle_paths import ue_publish_prefix  # type: ignore[import-not-found]

            return ue_publish_prefix(file_path).rstrip("/")
        except Exception:
            pass

    path = file_path.replace("\\", "/")
    lowered = path.lower()
    marker = "/setdec/"
    index = lowered.find(marker)
    if index != -1:
        suffix = path[index + len(marker) :].lstrip("/")
        return f"/Game/01_Assets/SETDEC/{suffix}"

    legacy_index = path.find("SETDEC")
    if legacy_index != -1:
        return f"/Game/01_Assets/{path[legacy_index:]}"

    return path


# ---------------------------------------------------------------------------
# Scene-description layout (config-driven)


@dataclass(frozen=True)
class SceneSchema:
    """In-memory representation of ``configs/setdec_scene_paths.json``."""

    category: str
    publish_segment: str
    filename: str
    default_variant: str
    version_padding: int


def default_scene_schema_path() -> Path:
    """Resolve the bundled schema path next to the package source tree."""
    here = Path(__file__).resolve()
    # core/paths.py -> core/ -> setdec_scene_description_io/ -> src/ -> repo root.
    repo_root = here.parents[3]
    return repo_root / "configs" / SCHEMA_FILENAME


def load_scene_schema(config_path: Path | None = None) -> SceneSchema:
    """Load the scene-description schema from disk (or the bundled default)."""
    config_path = config_path or default_scene_schema_path()
    raw = json.loads(Path(config_path).read_text(encoding="utf-8"))
    return SceneSchema(
        category=str(raw.get("category", "assets/env")),
        publish_segment=str(raw.get("publish_segment", "publish/unreal/sceneDescription")),
        filename=str(raw.get("filename", "{env}_{variant}_{version}.usda")),
        default_variant=str(raw.get("default_variant", "base")),
        version_padding=int(raw.get("version_padding", 3)),
    )


class ScenePaths:
    """Build scene-description paths for one show drive + schema.

    All paths use the canonical layout::

        {base_show_dir}/{show}/assets/env/{env}/publish/unreal/sceneDescription/{variant}/{version}/{env}_{variant}_{version}.usda
    """

    def __init__(self, base_show_dir: str, schema: SceneSchema) -> None:
        self.base_show_dir = (base_show_dir or "").replace("\\", "/").rstrip("/")
        self.schema = schema

    def show_root(self, show: str) -> str:
        return f"{self.base_show_dir}/{show}"

    def env_category_root(self, show: str) -> str:
        return f"{self.show_root(show)}/{self.schema.category}"

    def env_folder(self, show: str, env: str) -> str:
        return f"{self.env_category_root(show)}/{env}"

    def scene_description_root(self, show: str, env: str) -> str:
        return f"{self.env_folder(show, env)}/{self.schema.publish_segment}"

    def variant_folder(self, show: str, env: str, variant: str) -> str:
        return f"{self.scene_description_root(show, env)}/{variant}"

    def version_folder(self, show: str, env: str, variant: str, version: str) -> str:
        return f"{self.variant_folder(show, env, variant)}/{version}"

    def filename(self, env: str, variant: str, version: str) -> str:
        return self.schema.filename.format(env=env, variant=variant, version=version)

    def scene_description_file(self, show: str, env: str, variant: str, version: str) -> str:
        folder = self.version_folder(show, env, variant, version)
        return f"{folder}/{self.filename(env, variant, version)}"

    @staticmethod
    def list_subdirs(directory: str) -> list[str]:
        """Sorted child directory names, or ``[]`` when the path is missing."""
        if not directory or not os.path.isdir(directory):
            return []
        return sorted(
            name
            for name in os.listdir(directory)
            if os.path.isdir(os.path.join(directory, name))
        )

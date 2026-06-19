"""Publish layout detection and disk path helpers (no UI dependencies)."""

from __future__ import annotations

import os
import re

from genTools.studio_python_path import ensure_gen_tools_shared

ensure_gen_tools_shared()
from publish_bundle_paths import parse_version_folder_name  # type: ignore[import-not-found]

from assetTools.setdec_paths import normalize_disk_path

RIG_UNREAL_VERSION_RE = re.compile(r"^v(?P<version>\d+)$", re.IGNORECASE)
ASSET_MANAGER_CATEGORIES = frozenset({"chr", "prop", "env", "veh"})
DEFAULT_VARIANT_NAME = "main"


def list_subdirs(path: str) -> list[str]:
    if not os.path.isdir(path):
        return []
    return sorted(
        name
        for name in os.listdir(path)
        if os.path.isdir(os.path.join(path, name))
    )


def version_sort_key(version_label: str) -> int:
    if version_label.lower().startswith("v") and version_label[1:].isdigit():
        return int(version_label[1:])
    return 0


def is_asset_manager_version_path(path: str) -> bool:
    folder_name = os.path.basename(normalize_disk_path(path).rstrip("/\\"))
    return parse_version_folder_name(folder_name) is not None


def is_asset_manager_asset_root(path: str) -> bool:
    path = normalize_disk_path(path).rstrip("/\\")
    model_dir = os.path.join(path, "publish", "model")
    return os.path.isdir(model_dir) and not is_asset_manager_version_path(path)


def asset_manager_asset_root(path: str) -> str:
    path = normalize_disk_path(path).rstrip("/\\")
    if is_asset_manager_version_path(path):
        return normalize_disk_path(
            os.path.dirname(os.path.dirname(os.path.dirname(path)))
        )
    return path


def asset_manager_publish_variants(asset_root: str) -> dict[str, list[str]]:
    model_dir = os.path.join(normalize_disk_path(asset_root), "publish", "model")
    variants: dict[str, list[str]] = {}
    for folder in list_subdirs(model_dir):
        parsed = parse_version_folder_name(folder)
        if not parsed:
            continue
        _asset, _publish_type, variant, version = parsed
        variants.setdefault(variant, []).append(version)
    for variant, versions in variants.items():
        variants[variant] = sorted(set(versions), key=version_sort_key)
    return variants


def setdec_variants(asset_path: str) -> dict[str, list[str]]:
    variants: dict[str, list[str]] = {}
    for variant in list_subdirs(asset_path):
        versions = sorted(
            list_subdirs(os.path.join(asset_path, variant)),
            key=version_sort_key,
        )
        if versions:
            variants[variant] = versions
    return variants


def asset_manager_category_from_root(asset_root: str) -> str | None:
    parts = normalize_disk_path(asset_root).split("/")
    for idx, part in enumerate(parts):
        if part.lower() == "assets" and idx + 1 < len(parts):
            category = parts[idx + 1].lower()
            if category in ASSET_MANAGER_CATEGORIES:
                return category
    return None


def rig_unreal_root(asset_root: str) -> str:
    return normalize_disk_path(os.path.join(asset_root, "publish", "rig", "unreal"))


def rig_unreal_version_has_fbx(version_dir: str) -> bool:
    if not os.path.isdir(version_dir):
        return False
    return any(
        name.lower().endswith(".fbx")
        for name in os.listdir(version_dir)
        if os.path.isfile(os.path.join(version_dir, name))
    )


def rig_unreal_versions(asset_root: str) -> list[str]:
    unreal_root = rig_unreal_root(asset_root)
    if not os.path.isdir(unreal_root):
        return []
    versions = [
        version
        for version in list_subdirs(unreal_root)
        if RIG_UNREAL_VERSION_RE.match(version)
        and rig_unreal_version_has_fbx(os.path.join(unreal_root, version))
    ]
    return sorted(versions, key=version_sort_key)


def is_rig_unreal_asset_root(path: str) -> bool:
    return bool(rig_unreal_versions(path))


def publish_layout_for_path(path: str, *, layout_hint: str | None = None) -> str:
    if layout_hint == "rig_unreal":
        return "rig_unreal"
    if layout_hint == "asset_manager_model":
        return "asset_manager_model"
    if layout_hint == "setdec":
        return "setdec"
    if is_rig_unreal_asset_root(path):
        return "rig_unreal"
    if is_asset_manager_asset_root(path) or is_asset_manager_version_path(path):
        return "asset_manager_model"
    return "setdec"


def asset_display_name(path: str) -> str:
    return os.path.basename(normalize_disk_path(path).rstrip("/\\"))

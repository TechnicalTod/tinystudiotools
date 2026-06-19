"""Publish bundle path helpers aligned with GenTools/shared/publish_bundle_paths."""

from __future__ import annotations

import os
import re
from typing import Optional


def _ensure_publish_bundle_paths():
    try:
        from publish_bundle_paths import (  # type: ignore[import-not-found]
            StaticMeshPublishIdentity,
            bundle_paths,
            identity_from_base_path,
            identity_from_legacy_setdec_args,
            sm_prefixed_mesh_object_path,
        )
        return (
            StaticMeshPublishIdentity,
            bundle_paths,
            identity_from_base_path,
            identity_from_legacy_setdec_args,
            sm_prefixed_mesh_object_path,
        )
    except ImportError:
        from genTools.studio_python_path import ensure_gen_tools_shared

        ensure_gen_tools_shared()
        from publish_bundle_paths import (  # type: ignore[import-not-found]
            StaticMeshPublishIdentity,
            bundle_paths,
            identity_from_base_path,
            identity_from_legacy_setdec_args,
            sm_prefixed_mesh_object_path,
        )
        return (
            StaticMeshPublishIdentity,
            bundle_paths,
            identity_from_base_path,
            identity_from_legacy_setdec_args,
            sm_prefixed_mesh_object_path,
        )


(
    StaticMeshPublishIdentity,
    bundle_paths,
    identity_from_base_path,
    identity_from_legacy_setdec_args,
    sm_prefixed_mesh_object_path,
) = _ensure_publish_bundle_paths()


def resolve_identity(
    asset_path: str,
    variant: str,
    version: str,
    *,
    base_path: Optional[str] = None,
    asset_name: Optional[str] = None,
) -> StaticMeshPublishIdentity:
    if base_path and asset_name:
        return identity_from_base_path(base_path, asset_name, variant, version)
    return identity_from_legacy_setdec_args(asset_path, variant, version)


def build_unreal_mesh_import_path(asset_path: str, variant: str, version: str) -> str:
    """Content-browser folder for one published static mesh."""
    identity = identity_from_legacy_setdec_args(asset_path, variant, version)
    return bundle_paths(identity).ue_import_dir


def expected_ue_mesh_object_path(asset_path: str, variant: str, version: str) -> str:
    """Object path passed to ``unreal.load_asset`` for the imported static mesh."""
    identity = identity_from_legacy_setdec_args(asset_path, variant, version)
    return bundle_paths(identity).ue_mesh_object_path


def expected_ue_mesh_object_path_for_identity(identity: StaticMeshPublishIdentity) -> str:
    return bundle_paths(identity).ue_mesh_object_path


def udim_to_glob(path: Optional[str]) -> Optional[str]:
    if path is None:
        return path

    patterns = {
        "<udim>": "<udim>",
        "<tile>": "<tile>",
        "<uvtile>": "<uvtile>",
        "#": "#",
        "u<u>_v<v>": "<u>|<v>",
        "<frame0": "<frame0\\d+>",
        "<f>": "<f>",
    }

    lower = path.lower()
    has_pattern = False
    for pattern, regex_pattern in patterns.items():
        if pattern in lower:
            path = re.sub(regex_pattern, "*", path, flags=re.IGNORECASE)
            has_pattern = True

    if has_pattern:
        return path

    base = os.path.basename(path)
    matches = list(re.finditer(r"\d+", base))
    if matches:
        match = matches[-1]
        new_base = "{0}*{1}".format(base[: match.start()], base[match.end() :])
        head = os.path.dirname(path)
        return os.path.join(head, new_base)
    return path

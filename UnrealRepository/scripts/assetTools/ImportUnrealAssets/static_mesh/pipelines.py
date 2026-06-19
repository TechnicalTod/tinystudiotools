"""Static mesh publish import pipelines."""

from __future__ import annotations

from typing import Optional

import unreal

from ..materials.assignment import assign_setdec_static_mesh_materials
from ..publish import (
    StaticMeshPublishIdentity,
    identity_from_legacy_setdec_args,
    sm_prefixed_mesh_object_path,
    bundle_paths,
)
from ..types import WarnFn
from .import_mesh import import_static_mesh, mesh_object_path, published_fbx_path_for_identity
from .import_textures import import_static_mesh_textures
from .version_copy import copy_lightmap_and_materials_from_previous, get_previous_version_static_mesh


def resolve_static_mesh_object_path(identity: StaticMeshPublishIdentity) -> Optional[str]:
    """Return a loadable static mesh object path, including ``SM_`` renamed imports."""
    paths = bundle_paths(identity)
    for candidate in (paths.ue_mesh_object_path, sm_prefixed_mesh_object_path(identity)):
        if unreal.EditorAssetLibrary.load_asset(candidate):
            return candidate
    return None


def import_static_mesh_publish_pipeline(
    identity: StaticMeshPublishIdentity,
    *,
    warn: WarnFn,
    use_previous_version_settings: bool = False,
) -> Optional[str]:
    """Run mesh + textures + materials. Returns loadable UE static-mesh object path."""
    imported_mesh, unreal_mesh_import_path = import_static_mesh(identity, warn=warn)
    if not imported_mesh or unreal_mesh_import_path is None:
        return None

    mesh_path = mesh_object_path(imported_mesh)

    if use_previous_version_settings:
        previous_mesh = get_previous_version_static_mesh(
            unreal_mesh_import_path,
            identity.version,
        )
        if previous_mesh:
            loaded_new_mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
            if loaded_new_mesh:
                copy_lightmap_and_materials_from_previous(
                    unreal_mesh_import_path,
                    previous_mesh,
                    loaded_new_mesh,
                )
                return resolve_static_mesh_object_path(identity) or mesh_path
        unreal.log_warning(
            "No previous version mesh found. Falling back to default import."
        )

    texture_result = import_static_mesh_textures(
        identity, unreal_mesh_import_path, warn=warn
    )
    assign_setdec_static_mesh_materials(
        imported_mesh,
        unreal_mesh_import_path,
        texture_result.imported_textures,
        orma_channels_by_slot=texture_result.orma_channels_by_slot,
        scalar_values_by_slot=texture_result.scalar_values_by_slot,
    )
    return resolve_static_mesh_object_path(identity)


def import_setdec_static_mesh_pipeline(
    asset_path: str,
    variant: str,
    version: str,
    *,
    warn: WarnFn,
    use_previous_version_settings: bool = False,
) -> Optional[str]:
    identity = identity_from_legacy_setdec_args(asset_path, variant, version)
    return import_static_mesh_publish_pipeline(
        identity,
        warn=warn,
        use_previous_version_settings=use_previous_version_settings,
    )


def ensure_static_mesh_imported(
    identity: StaticMeshPublishIdentity,
    *,
    warn: WarnFn,
) -> Optional[str]:
    """Return UE mesh object path, importing from publish disk when missing."""
    resolved_path = resolve_static_mesh_object_path(identity)
    if resolved_path:
        return resolved_path

    if published_fbx_path_for_identity(identity, warn=warn) is None:
        return None

    import_static_mesh_publish_pipeline(identity, warn=warn)
    return resolve_static_mesh_object_path(identity)


def ensure_setdec_static_mesh_imported(
    asset_path: str,
    variant: str,
    version: str,
    *,
    warn: WarnFn,
) -> Optional[str]:
    identity = identity_from_legacy_setdec_args(asset_path, variant, version)
    return ensure_static_mesh_imported(identity, warn=warn)

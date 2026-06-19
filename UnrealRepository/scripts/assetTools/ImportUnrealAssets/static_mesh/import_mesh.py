"""Static mesh FBX import and metadata tagging."""

from __future__ import annotations

import os
from typing import List, Optional, Tuple

import unreal

import genTools.genUnrealImportUtils as genUnrealImportUtils

from ..publish import StaticMeshPublishIdentity, bundle_paths, identity_from_legacy_setdec_args
from ..types import WarnFn


def mesh_object_path(imported_mesh: List[str] | str) -> str:
    if isinstance(imported_mesh, list):
        return imported_mesh[0].split(".")[0]
    return str(imported_mesh).split(".")[0]


def published_fbx_path_for_identity(
    identity: StaticMeshPublishIdentity,
    *,
    warn: WarnFn,
) -> Optional[str]:
    paths = bundle_paths(identity)
    fbx_path = paths.fbx_file.replace("\\", "/")
    if os.path.isfile(fbx_path):
        if os.path.getsize(fbx_path) < 512:
            warn(
                "FBX file is empty or too small for {}: {}".format(
                    identity.asset_name, fbx_path
                )
            )
            return None
        return fbx_path

    fbx_dir = paths.fbx_dir.replace("\\", "/")
    if not os.path.isdir(fbx_dir):
        warn("No FBX files found in {} publish directory".format(identity.asset_name))
        return None

    fbx_list = [fbx for fbx in os.listdir(fbx_dir) if fbx.endswith(".fbx")]
    if len(fbx_list) > 1:
        warn("Found too many FBX files in {} publish directory".format(identity.asset_name))
        return None
    if len(fbx_list) == 0:
        warn("No FBX files found in {} publish directory".format(identity.asset_name))
        return None
    fallback_path = "{}{}".format(fbx_dir, fbx_list[0])
    if os.path.getsize(fallback_path) < 512:
        warn(
            "FBX file is empty or too small for {}: {}".format(
                identity.asset_name, fallback_path
            )
        )
        return None
    return fallback_path


def published_fbx_path(
    asset_path: str,
    variant: str,
    version: str,
    *,
    warn: WarnFn,
) -> Optional[str]:
    identity = identity_from_legacy_setdec_args(asset_path, variant, version)
    return published_fbx_path_for_identity(identity, warn=warn)


def tag_imported_static_mesh_metadata(
    imported_mesh_paths: List[str],
    identity: StaticMeshPublishIdentity,
) -> None:
    """Persist Maya-compatible publish metadata on imported static meshes."""
    for imported_path in imported_mesh_paths:
        object_path = imported_path.split(".")[0]
        mesh_asset = unreal.EditorAssetLibrary.load_asset(object_path)
        if mesh_asset is None:
            continue
        unreal.EditorAssetLibrary.set_metadata_tag(
            mesh_asset, "FBX.assetName", identity.asset_name
        )
        unreal.EditorAssetLibrary.set_metadata_tag(
            mesh_asset, "FBX.basePath", identity.base_path
        )
        unreal.EditorAssetLibrary.set_metadata_tag(mesh_asset, "FBX.version", identity.version)
        unreal.EditorAssetLibrary.set_metadata_tag(
            mesh_asset, "FBX.variantName", identity.variant
        )
        unreal.EditorAssetLibrary.save_asset(object_path)


def rename_static_mesh_sm_prefix(mesh_object_path: str, unreal_mesh_import_path: str) -> str:
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_object_path)
    if mesh is None:
        return mesh_object_path

    original_name = mesh.get_name()
    if original_name.startswith("SM_"):
        return mesh.get_path_name().split(".")[0]

    new_name = "SM_{}".format(original_name)
    new_path = "{}/{}".format(unreal_mesh_import_path.rstrip("/"), new_name)
    unreal.EditorAssetLibrary.rename_asset(mesh.get_path_name(), new_path)
    unreal.EditorAssetLibrary.save_asset(new_path)
    return new_path


def import_static_mesh(
    identity: StaticMeshPublishIdentity,
    *,
    warn: WarnFn,
) -> Tuple[Optional[List[str]], Optional[str]]:
    """Import the published FBX. Returns ``(imported_paths, unreal_mesh_import_path)``."""
    fbx_asset_path = published_fbx_path_for_identity(identity, warn=warn)
    if fbx_asset_path is None:
        return None, None

    paths = bundle_paths(identity)
    import_mesh_task = genUnrealImportUtils.buildImportTask(
        fbx_asset_path,
        paths.ue_import_dir,
        genUnrealImportUtils.buildStaticMeshImportOptions(),
    )
    imported_mesh = genUnrealImportUtils.executeImportTasks([import_mesh_task])
    tag_imported_static_mesh_metadata(imported_mesh, identity)
    return imported_mesh, paths.ue_import_dir


def import_setdec_static_mesh(
    asset_path: str,
    variant: str,
    version: str,
    *,
    warn: WarnFn,
) -> Tuple[Optional[List[str]], Optional[str]]:
    identity = identity_from_legacy_setdec_args(asset_path, variant, version)
    return import_static_mesh(identity, warn=warn)

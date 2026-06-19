"""Skeletal mesh FBX import."""

from __future__ import annotations

import os
from typing import Optional, Tuple

import genTools.genUnrealImportUtils as genUnrealImportUtils
import genTools.genUnrealUtils as genUnrealUtils

from ..types import WarnFn
from .paths import resolve_skeletal_publish_paths


def import_skeletal_mesh(
    asset_path: str,
    variant_name: str,
    version_number: str,
    *,
    layout: str,
    warn: WarnFn = genUnrealUtils.warningPopup,
) -> Tuple[Optional[list], str]:
    asset_name = asset_path.split("/")[-1]
    published_fbx_path, _published_tex_path, unreal_mesh_import_path = (
        resolve_skeletal_publish_paths(
            asset_path,
            variant_name,
            version_number,
            layout=layout,
        )
    )
    if not os.path.isdir(published_fbx_path):
        warn(
            "Publish folder not found for {}: {}".format(asset_name, published_fbx_path)
        )
        return None, unreal_mesh_import_path

    fbx_list = [
        fbx
        for fbx in os.listdir(published_fbx_path)
        if fbx.lower().endswith(".fbx")
        and os.path.isfile(os.path.join(published_fbx_path, fbx))
    ]
    if len(fbx_list) > 1:
        warn("Found too many FBX files in {} publish directory".format(asset_name))
    if len(fbx_list) == 0:
        warn("No FBX files found in {} publish directory".format(asset_name))
        return None, unreal_mesh_import_path

    fbx_asset_path = published_fbx_path + fbx_list[0]
    import_mesh_task = genUnrealImportUtils.buildImportTask(
        fbx_asset_path,
        unreal_mesh_import_path,
        genUnrealImportUtils.buildSkeletalMeshImportOptions(),
    )
    imported_mesh = genUnrealImportUtils.executeImportTasks([import_mesh_task])
    return imported_mesh, unreal_mesh_import_path

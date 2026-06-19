"""Skeletal mesh texture import from publish disk."""

from __future__ import annotations

import os
from typing import Optional

import unreal

import genTools.genUnrealImportUtils as genUnrealImportUtils

from assetTools.setdec_paths import normalize_disk_path

from .paths import resolve_skeletal_publish_paths


def import_skeletal_textures(
    asset_path: str,
    variant_name: str,
    version_number: str,
    unreal_mesh_import_path: str,
    *,
    layout: str,
) -> Optional[list]:
    tex_list = []
    _published_fbx_path, published_tex_path, _ue_import_dir = resolve_skeletal_publish_paths(
        asset_path,
        variant_name,
        version_number,
        layout=layout,
    )
    if os.path.isdir(published_tex_path):
        for texture in os.listdir(published_tex_path):
            texture_path = os.path.join(published_tex_path, texture)
            if not os.path.isfile(texture_path):
                continue
            if texture.lower().endswith((".png", ".jpg", ".jpeg", ".tga")):
                tex_list.append(normalize_disk_path(texture_path))

    unreal_tex_import_path = "{}/TEX".format(unreal_mesh_import_path)
    unreal_mat_import_path = "{}/MAT".format(unreal_mesh_import_path)

    if not tex_list:
        unreal.EditorAssetLibrary.make_directory(unreal_tex_import_path)
        unreal.EditorAssetLibrary.make_directory(unreal_mat_import_path)
        return None

    tex_import_task_list = []
    for sorted_texture in tex_list:
        tex_import_task_list.append(
            genUnrealImportUtils.buildImportTask(
                sorted_texture,
                unreal_tex_import_path,
            )
        )
    return genUnrealImportUtils.executeImportTasks(tex_import_task_list)

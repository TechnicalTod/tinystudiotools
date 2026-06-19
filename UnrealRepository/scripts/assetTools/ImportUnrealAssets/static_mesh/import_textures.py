"""Static mesh USD texture collection and import."""

from __future__ import annotations

import glob
import os
from typing import Dict, FrozenSet, List, Optional

import unreal

import genTools.genUnrealImportUtils as genUnrealImportUtils

from ..constants import ORMA_PARAMETERS, USD_PREVIEW_PARAMETER_LIST
from ..orma.pack import create_orma_texture
from ..publish import StaticMeshPublishIdentity, bundle_paths, identity_from_legacy_setdec_args, udim_to_glob
from ..types import StaticMeshTextureImportResult, WarnFn
from ..usd import shader_data


def resolve_usd_texture_path(texture: str) -> Optional[str]:
    """Resolve one USD texture path, preferring UDIM tile 1001 when present."""
    if texture.endswith(".<UDIM>.png"):
        glob_path = udim_to_glob(texture)
        if not glob_path:
            return None
        matches = sorted(glob.glob(glob_path))
        if not matches:
            return None
        for match in matches:
            if ".1001." in os.path.basename(match) or match.endswith(".1001.png"):
                return match
        return matches[0]
    return texture


def append_usd_texture_paths(tex_list: List[str], texture: str) -> None:
    if texture.endswith(".<UDIM>.png"):
        glob_path = udim_to_glob(texture)
        if glob_path:
            tex_list.extend(sorted(glob.glob(glob_path)))
        return
    tex_list.append(texture)


def finalize_scalar_values_by_slot(
    shader_data: dict,
    orma_channels_by_slot: Dict[str, FrozenSet[str]],
) -> Dict[str, Dict[str, object]]:
    """Drop scalar fallbacks that are superseded by imported textures or packed ORMA."""
    scalar_values_by_slot: Dict[str, Dict[str, object]] = {}
    for shader_name, shader_entry in shader_data.items():
        scalars = dict(shader_entry.get("scalars", {}))
        textures = shader_entry.get("textures", {})
        orma_channels = orma_channels_by_slot.get(shader_name, frozenset())

        if "diffuseColor" in textures:
            scalars.pop("albedo_color", None)
        if "emissiveColor" in textures:
            scalars.pop("emissive_color", None)
        if "roughness" in textures or "roughness" in orma_channels:
            scalars.pop("roughness", None)
        if "metallic" in textures or "metallic" in orma_channels:
            scalars.pop("metallic", None)

        if scalars:
            scalar_values_by_slot[shader_name] = scalars
    return scalar_values_by_slot


def collect_static_mesh_disk_textures(
    shader_data: dict,
    *,
    pack_orma: bool = True,
) -> tuple[List[str], Dict[str, FrozenSet[str]], Dict[str, Dict[str, object]]]:
    """Collect disk texture paths from USD shader data, optionally packing ORMA per slot."""
    tex_list: List[str] = []
    orma_channels_by_slot: Dict[str, FrozenSet[str]] = {}
    preview_parameters = USD_PREVIEW_PARAMETER_LIST.get("USDPreviewMaterial", {})

    for shader_name, shader_entry in shader_data.items():
        texture_dict = shader_entry.get("textures", {})
        orma_sources: Dict[str, str] = {}

        for parameter, parameter_data in preview_parameters.items():
            maya_parameter_name = parameter_data.get("mayaParameter")
            texture = texture_dict.get(maya_parameter_name)
            if not texture:
                continue

            if pack_orma and parameter in ORMA_PARAMETERS:
                resolved = resolve_usd_texture_path(texture)
                if resolved:
                    orma_sources[parameter] = resolved
                continue

            append_usd_texture_paths(tex_list, texture)

        if pack_orma and orma_sources:
            orma_channels_by_slot[shader_name] = frozenset(orma_sources.keys())
            tex_list.append(
                create_orma_texture(
                    occlusion_path=orma_sources.get("ao"),
                    roughness_path=orma_sources.get("roughness"),
                    metallic_path=orma_sources.get("metallic"),
                    alpha_path=orma_sources.get("opacity"),
                )
            )

    scalar_values_by_slot = finalize_scalar_values_by_slot(shader_data, orma_channels_by_slot)
    return tex_list, orma_channels_by_slot, scalar_values_by_slot


def import_static_mesh_textures(
    identity: StaticMeshPublishIdentity,
    unreal_mesh_import_path: str,
    *,
    warn: WarnFn,
    pack_orma: bool = True,
) -> StaticMeshTextureImportResult:
    """Import textures from the published USD shader graph."""
    empty_dirs = StaticMeshTextureImportResult(None, {}, {})
    paths = bundle_paths(identity)
    usd_dir = paths.usd_dir.replace("\\", "/")
    if not os.path.isdir(usd_dir):
        unreal.EditorAssetLibrary.make_directory(f"{unreal_mesh_import_path}/TEX")
        unreal.EditorAssetLibrary.make_directory(f"{unreal_mesh_import_path}/MAT")
        return empty_dirs

    usd_files = [name for name in os.listdir(usd_dir) if name.endswith((".usd", ".usda"))]
    if not usd_files:
        unreal.EditorAssetLibrary.make_directory(f"{unreal_mesh_import_path}/TEX")
        unreal.EditorAssetLibrary.make_directory(f"{unreal_mesh_import_path}/MAT")
        return empty_dirs

    usd_shader_data = shader_data.get_shader_data(usd_dir + usd_files[0])
    try:
        tex_list, orma_channels_by_slot, scalar_values_by_slot = collect_static_mesh_disk_textures(
            usd_shader_data,
            pack_orma=pack_orma,
        )
    except Exception as exc:
        warn("Failed to collect static mesh textures for {}: {}".format(identity.asset_name, exc))
        return empty_dirs

    unreal_tex_import_path = "{}/TEX".format(unreal_mesh_import_path)
    unreal_mat_import_path = "{}/MAT".format(unreal_mesh_import_path)

    if len(tex_list) == 0:
        unreal.EditorAssetLibrary.make_directory(unreal_tex_import_path)
        unreal.EditorAssetLibrary.make_directory(unreal_mat_import_path)
        if scalar_values_by_slot:
            return StaticMeshTextureImportResult(None, orma_channels_by_slot, scalar_values_by_slot)
        return empty_dirs

    tex_import_task_list = []
    for sorted_texture in tex_list:
        tex_import_task_list.append(
            genUnrealImportUtils.buildImportTask(sorted_texture, unreal_tex_import_path)
        )
    imported_textures = genUnrealImportUtils.executeImportTasks(tex_import_task_list)
    return StaticMeshTextureImportResult(
        imported_textures,
        orma_channels_by_slot,
        scalar_values_by_slot,
    )


def import_setdec_textures(
    asset_path: str,
    variant: str,
    version: str,
    unreal_mesh_import_path: str,
    *,
    warn: WarnFn,
    pack_orma: bool = True,
) -> StaticMeshTextureImportResult:
    identity = identity_from_legacy_setdec_args(asset_path, variant, version)
    return import_static_mesh_textures(
        identity,
        unreal_mesh_import_path,
        warn=warn,
        pack_orma=pack_orma,
    )

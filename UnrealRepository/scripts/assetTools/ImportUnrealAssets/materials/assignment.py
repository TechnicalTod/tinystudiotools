"""Material instance creation and mesh assignment."""

from __future__ import annotations

from typing import Dict, FrozenSet, List, Optional

import unreal

from ..constants import MASTER_MATERIAL_PATH
from ..types import WarnFn
from ..static_mesh.import_mesh import mesh_object_path, rename_static_mesh_sm_prefix
from .master_standard import (
    apply_orma_texture_to_material_instance,
    apply_scalar_values_to_material_instance,
    apply_texture_to_material_instance,
    set_material_instance_toggle,
)
from .slot_matching import (
    lookup_orma_channels_for_slot,
    lookup_scalar_values_for_slot,
    texture_matches_material_slot,
)


def material_instance_name(material_slot_name: str) -> str:
    slot = str(material_slot_name)
    if "_" in slot:
        return "MI_" + slot.split("_", 1)[1]
    return "MI_" + slot


def assign_mesh_materials(
    imported_mesh: List[str],
    unreal_mesh_import_path: str,
    imported_textures: Optional[List[str]],
    asset_type: str,
    *,
    warn: Optional[WarnFn] = None,
    orma_channels_by_slot: Optional[Dict[str, FrozenSet[str]]] = None,
    scalar_values_by_slot: Optional[Dict[str, Dict[str, object]]] = None,
) -> Optional[str]:
    """Create material instances and assign them to an imported mesh.

    Returns the final static mesh object path when ``asset_type`` is ``Static Mesh``,
    otherwise ``None``.
    """
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    unreal_eal = unreal.EditorAssetLibrary()
    mesh_path = mesh_object_path(imported_mesh)
    loaded_imported_mesh = unreal_eal.load_asset(mesh_path)
    if loaded_imported_mesh is None:
        if warn:
            warn("Could not load imported mesh at {}".format(mesh_path))
        return None

    loaded_master_material = unreal_eal.load_asset(MASTER_MATERIAL_PATH)
    if loaded_master_material is None and warn:
        warn("Could not load master material at {}".format(MASTER_MATERIAL_PATH))

    unreal_mat_import_path = "{}/MAT".format(unreal_mesh_import_path)

    loaded_tex_list = []
    material_instances = []
    if imported_textures is not None:
        for texture_path in imported_textures:
            texture_path = texture_path.split(".")[0]
            loaded_texture = unreal_eal.load_asset(texture_path)
            if loaded_texture is not None:
                loaded_tex_list.append(loaded_texture)

    if asset_type == "Static Mesh":
        material_type_function = loaded_imported_mesh.static_materials
    elif asset_type == "Skeletal Mesh":
        material_type_function = loaded_imported_mesh.materials
        material_array = unreal.Array(unreal.SkeletalMaterial)
    else:
        if warn:
            warn("Unsupported asset type for material assignment: {}".format(asset_type))
        return None

    single_material_slot = len(material_type_function) == 1

    for material in material_type_function:
        index = material_type_function.index(material)
        new_mat_name = material_instance_name(material.material_slot_name)
        material_instance = asset_tools.create_asset(
            new_mat_name,
            unreal_mat_import_path,
            unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew(),
        )
        material_instances.append(material_instance)
        if loaded_master_material is not None:
            material_instance.set_editor_property("parent", loaded_master_material)

        if asset_type == "Static Mesh":
            loaded_imported_mesh.set_material(index, material_instance)
        elif asset_type == "Skeletal Mesh":
            new_sk_material = unreal.SkeletalMaterial()
            slot_name = material.get_editor_property("material_slot_name")
            new_sk_material.set_editor_property("material_slot_name", slot_name)
            new_sk_material.set_editor_property("material_interface", material_instance)
            material_array.append(new_sk_material)

        if loaded_tex_list:
            slot_name = str(material.material_slot_name)
            slot_orma_channels = lookup_orma_channels_for_slot(
                orma_channels_by_slot,
                slot_name,
                single_material_slot=single_material_slot,
            )
            assigned_count = 0
            for texture in loaded_tex_list:
                if not texture_matches_material_slot(
                    texture.get_name(),
                    slot_name,
                    orma_channels_by_slot=orma_channels_by_slot,
                    single_material_slot=single_material_slot,
                ):
                    continue

                if "_orma" in texture.get_name().lower():
                    apply_orma_texture_to_material_instance(
                        material_instance,
                        texture,
                        orma_channels=slot_orma_channels,
                    )
                else:
                    apply_texture_to_material_instance(material_instance, texture)
                assigned_count += 1

            if assigned_count == 0 and not lookup_scalar_values_for_slot(
                scalar_values_by_slot,
                slot_name,
                single_material_slot=single_material_slot,
            ):
                unreal.log_warning(
                    "No imported textures matched material slot '{}' on {}.".format(
                        slot_name,
                        loaded_imported_mesh.get_name(),
                    )
                )

            slot_scalars = lookup_scalar_values_for_slot(
                scalar_values_by_slot,
                slot_name,
                single_material_slot=single_material_slot,
            )
            if slot_scalars:
                apply_scalar_values_to_material_instance(material_instance, slot_scalars)
        else:
            slot_name = str(material.material_slot_name)
            slot_scalars = lookup_scalar_values_for_slot(
                scalar_values_by_slot,
                slot_name,
                single_material_slot=single_material_slot,
            )
            if slot_scalars:
                apply_scalar_values_to_material_instance(material_instance, slot_scalars)
            else:
                set_material_instance_toggle(material_instance, "Use Albedo Texture?", True)

    if asset_type == "Skeletal Mesh":
        loaded_imported_mesh.set_editor_property("materials", material_array)

    new_assets = [loaded_tex_list, material_instances, [loaded_imported_mesh]]
    if asset_type == "Skeletal Mesh":
        physics_asset = loaded_imported_mesh.get_editor_property("physics_asset")
        skeleton_asset = loaded_imported_mesh.get_editor_property("skeleton")
        new_assets.append([physics_asset])
        new_assets.append([skeleton_asset])

    for asset_list in new_assets:
        for asset in asset_list:
            if asset is None:
                continue
            asset_name_clean = asset.get_path_name().split(".")[0]
            unreal.EditorAssetLibrary.save_asset(asset_name_clean)

    if asset_type == "Static Mesh":
        return rename_static_mesh_sm_prefix(mesh_path, unreal_mesh_import_path)
    return None


def assign_setdec_static_mesh_materials(
    imported_mesh: List[str],
    unreal_mesh_import_path: str,
    imported_textures: Optional[List[str]],
    *,
    orma_channels_by_slot: Optional[Dict[str, FrozenSet[str]]] = None,
    scalar_values_by_slot: Optional[Dict[str, Dict[str, object]]] = None,
) -> None:
    """Create material instances and assign them to the imported static mesh."""
    assign_mesh_materials(
        imported_mesh,
        unreal_mesh_import_path,
        imported_textures,
        "Static Mesh",
        orma_channels_by_slot=orma_channels_by_slot,
        scalar_values_by_slot=scalar_values_by_slot,
    )

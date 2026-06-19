"""Copy lightmap and materials from a prior published static mesh version."""

from __future__ import annotations

from typing import Optional

import unreal

from .import_mesh import rename_static_mesh_sm_prefix


def get_previous_version_static_mesh(
    unreal_mesh_import_path: str,
    current_version_number: str,
) -> Optional[unreal.StaticMesh]:
    """Find the most recent static mesh from a prior version folder under the variant path."""
    variant_path = unreal_mesh_import_path.rsplit("/", 1)[0]

    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    asset_registry.scan_paths_synchronous([variant_path], True)

    subfolders = unreal.EditorAssetLibrary.list_assets(
        variant_path, recursive=False, include_folder=True
    )
    version_folders = set()
    for path in subfolders:
        if path.endswith("/"):
            version_folder = path.rstrip("/").split("/")[-1]
            if version_folder != current_version_number and version_folder.startswith("v"):
                version_folders.add(version_folder)

    if not version_folders:
        unreal.log_warning("No version folders found in {}".format(variant_path))
        return None

    sorted_versions = sorted(version_folders, reverse=True)
    for version in sorted_versions:
        version_path = "{}/{}".format(variant_path, version)
        assets_in_version = unreal.EditorAssetLibrary.list_assets(
            version_path, recursive=False, include_folder=False
        )
        for asset_path in assets_in_version:
            asset = unreal.EditorAssetLibrary.load_asset(asset_path)
            if isinstance(asset, unreal.StaticMesh):
                unreal.log(
                    "Found previous static mesh in {}: {}".format(version_path, asset_path)
                )
                return asset

    unreal.log_warning(
        "No static mesh found in any previous version folder under {}".format(variant_path)
    )
    return None


def copy_lightmap_and_materials_from_previous(
    unreal_mesh_import_path: str,
    from_mesh: unreal.StaticMesh,
    to_mesh: unreal.StaticMesh,
) -> str:
    """Copy lightmap, LOD build settings, and material slots from a prior version mesh."""
    if from_mesh is None or to_mesh is None:
        return to_mesh.get_path_name().split(".")[0] if to_mesh else ""

    lightmap_res = from_mesh.get_editor_property("light_map_resolution")
    to_mesh.set_editor_property("light_map_resolution", lightmap_res)

    static_mesh_editor = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    from_build_settings = static_mesh_editor.get_lod_build_settings(from_mesh, 0)
    static_mesh_editor.set_lod_build_settings(to_mesh, 0, from_build_settings)

    from_materials = from_mesh.get_editor_property("static_materials")
    for index, material_slot in enumerate(from_materials):
        to_mesh.set_material(index, material_slot.material_interface)

    to_mesh.modify()
    mesh_object_path = to_mesh.get_path_name().split(".")[0]
    unreal.EditorAssetLibrary.save_asset(mesh_object_path)
    return rename_static_mesh_sm_prefix(mesh_object_path, unreal_mesh_import_path)

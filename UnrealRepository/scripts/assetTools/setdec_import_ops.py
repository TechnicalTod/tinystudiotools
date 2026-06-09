"""Static-mesh publish import operations shared by manual importer UI and scene-description IO.

UE destination paths must stay aligned with
``publish_bundle_paths`` in GenTools/shared and
``setdec_scene_description_io.core.paths.complete_path``.
"""

from __future__ import annotations

import glob
import os
import sys
from typing import Callable, List, Optional, Tuple

import unreal

import assetTools.getUSDTexturePaths as getUSDTexturePaths
import genTools.genUnrealImportUtils as genUnrealImportUtils

WarnFn = Callable[[str], None]

USD_PREVIEW_PARAMETER_LIST = {
    "USDPreviewMaterial": {
        "diffuse": {
            "suffix": "Diffuse",
            "mayaParameter": "diffuseColor",
            "fileNodeParameter": "outColor",
        },
        "emissive": {
            "suffix": "Emissive",
            "mayaParameter": "emissiveColor",
            "fileNodeParameter": "outColor",
        },
        "ao": {"suffix": "AO", "mayaParameter": "occlusion", "fileNodeParameter": "outAlpha"},
        "opacity": {
            "suffix": "Opacity.",
            "mayaParameter": "opacity",
            "fileNodeParameter": "outAlpha",
        },
        "metallic": {
            "suffix": "Metallic",
            "mayaParameter": "metallic",
            "fileNodeParameter": "outAlpha",
        },
        "roughness": {
            "suffix": "Roughness",
            "mayaParameter": "roughness",
            "fileNodeParameter": "outAlpha",
        },
        "normal": {"suffix": "Normal", "mayaParameter": "normal", "fileNodeParameter": "outColor"},
        "subsurface": {
            "suffix": "Translucency",
            "mayaParameter": "clearcoat",
            "fileNodeParameter": "outAlpha",
        },
        "displacement": {
            "suffix": "Displacement",
            "mayaParameter": "displacement",
            "fileNodeParameter": "outAlpha",
        },
    }
}


def _ensure_publish_bundle_paths():
    try:
        from publish_bundle_paths import (  # type: ignore[import-not-found]
            StaticMeshPublishIdentity,
            bundle_paths,
            identity_from_base_path,
            identity_from_legacy_setdec_args,
        )
        return StaticMeshPublishIdentity, bundle_paths, identity_from_base_path, identity_from_legacy_setdec_args
    except ImportError:
        from genTools.studio_python_path import ensure_gen_tools_shared

        ensure_gen_tools_shared()
        from publish_bundle_paths import (  # type: ignore[import-not-found]
            StaticMeshPublishIdentity,
            bundle_paths,
            identity_from_base_path,
            identity_from_legacy_setdec_args,
        )
        return StaticMeshPublishIdentity, bundle_paths, identity_from_base_path, identity_from_legacy_setdec_args


(
    StaticMeshPublishIdentity,
    bundle_paths,
    identity_from_base_path,
    identity_from_legacy_setdec_args,
) = _ensure_publish_bundle_paths()


def _resolve_identity(
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

    import re

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


def _published_fbx_path_for_identity(
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


def _published_fbx_path(
    asset_path: str,
    variant: str,
    version: str,
    *,
    warn: WarnFn,
) -> Optional[str]:
    identity = identity_from_legacy_setdec_args(asset_path, variant, version)
    return _published_fbx_path_for_identity(identity, warn=warn)


def import_static_mesh(
    identity: StaticMeshPublishIdentity,
    *,
    warn: WarnFn,
) -> Tuple[Optional[List[str]], Optional[str]]:
    """Import the published FBX. Returns ``(imported_paths, unreal_mesh_import_path)``."""
    fbx_asset_path = _published_fbx_path_for_identity(identity, warn=warn)
    if fbx_asset_path is None:
        return None, None

    paths = bundle_paths(identity)
    import_mesh_task = genUnrealImportUtils.buildImportTask(
        fbx_asset_path,
        paths.ue_import_dir,
        genUnrealImportUtils.buildStaticMeshImportOptions(),
    )
    imported_mesh = genUnrealImportUtils.executeImportTasks([import_mesh_task])
    _tag_imported_static_mesh_metadata(imported_mesh, identity)
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


def _tag_imported_static_mesh_metadata(
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


def import_static_mesh_textures(
    identity: StaticMeshPublishIdentity,
    unreal_mesh_import_path: str,
    *,
    warn: WarnFn,
) -> Optional[List[str]]:
    """Import textures from the published USD shader graph."""
    del warn
    tex_list: List[str] = []
    paths = bundle_paths(identity)
    usd_dir = paths.usd_dir.replace("\\", "/")
    if not os.path.isdir(usd_dir):
        unreal.EditorAssetLibrary.make_directory(f"{unreal_mesh_import_path}/TEX")
        unreal.EditorAssetLibrary.make_directory(f"{unreal_mesh_import_path}/MAT")
        return None

    usd_files = [name for name in os.listdir(usd_dir) if name.endswith((".usd", ".usda"))]
    if not usd_files:
        unreal.EditorAssetLibrary.make_directory(f"{unreal_mesh_import_path}/TEX")
        unreal.EditorAssetLibrary.make_directory(f"{unreal_mesh_import_path}/MAT")
        return None

    usd_shader_dict = getUSDTexturePaths.get_paths(usd_dir + usd_files[0])
    for shader_name in usd_shader_dict:
        texture_dict = usd_shader_dict.get(shader_name)
        for parameter in USD_PREVIEW_PARAMETER_LIST.get("USDPreviewMaterial"):
            maya_parameter_name = (
                USD_PREVIEW_PARAMETER_LIST.get("USDPreviewMaterial")
                .get(parameter)
                .get("mayaParameter")
            )
            texture = texture_dict.get(maya_parameter_name)
            if texture:
                if texture.endswith(".<UDIM>.png"):
                    glob_path = udim_to_glob(texture)
                    for tex in glob.glob(glob_path):
                        tex_list.append(tex)
                else:
                    tex_list.append(texture)

    unreal_tex_import_path = "{}/TEX".format(unreal_mesh_import_path)
    unreal_mat_import_path = "{}/MAT".format(unreal_mesh_import_path)

    if len(tex_list) == 0:
        unreal.EditorAssetLibrary.make_directory(unreal_tex_import_path)
        unreal.EditorAssetLibrary.make_directory(unreal_mat_import_path)
        return None

    tex_import_task_list = []
    for sorted_texture in tex_list:
        tex_import_task_list.append(
            genUnrealImportUtils.buildImportTask(sorted_texture, unreal_tex_import_path)
        )
    return genUnrealImportUtils.executeImportTasks(tex_import_task_list)


def import_setdec_textures(
    asset_path: str,
    variant: str,
    version: str,
    unreal_mesh_import_path: str,
    *,
    warn: WarnFn,
) -> Optional[List[str]]:
    identity = identity_from_legacy_setdec_args(asset_path, variant, version)
    return import_static_mesh_textures(identity, unreal_mesh_import_path, warn=warn)


def _material_instance_name(material_slot_name: str) -> str:
    slot = str(material_slot_name)
    if "_" in slot:
        return "MI_" + slot.split("_", 1)[1]
    return "MI_" + slot


def assign_setdec_static_mesh_materials(
    imported_mesh: List[str],
    unreal_mesh_import_path: str,
    imported_textures: Optional[List[str]],
) -> None:
    """Create material instances and assign them to the imported static mesh."""
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    unreal_eal = unreal.EditorAssetLibrary()
    mesh_object_path = imported_mesh[0].split(".")[0]
    loaded_imported_mesh = unreal_eal.load_asset(mesh_object_path)
    loaded_master_material = unreal_eal.load_asset(
        "/Game/03_Shared/MasterMaterials/M_BaseMaterial_Standard_VT"
    )
    unreal_mat_import_path = "{}/MAT".format(unreal_mesh_import_path)

    loaded_tex_list = []
    material_instances = []
    if imported_textures is not None:
        for texture_path in imported_textures:
            texture_path = texture_path.split(".")[0]
            loaded_texture = unreal_eal.load_asset(texture_path)
            loaded_tex_list.append(loaded_texture)

    material_type_function = loaded_imported_mesh.static_materials

    for material in material_type_function:
        index = material_type_function.index(material)
        new_mat_name = _material_instance_name(material.material_slot_name)
        material_instance = asset_tools.create_asset(
            new_mat_name,
            unreal_mat_import_path,
            unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew(),
        )
        material_instances.append(material_instance)
        material_instance.set_editor_property("parent", loaded_master_material)
        loaded_imported_mesh.set_material(index, material_instance)

        if len(loaded_tex_list) != 0:
            for texture in loaded_tex_list:
                if str(material.material_slot_name) in texture.get_name():
                    parameter_name = texture.get_name().split("_")[-1]
                    if parameter_name in ("AO", "Metallic", "Roughness"):
                        texture.set_editor_property("srgb", 0)
                    unreal.MaterialEditingLibrary.set_material_instance_static_switch_parameter_value(
                        material_instance,
                        "use{}Texture".format(parameter_name),
                        True,
                    )
                    unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
                        material_instance, parameter_name, texture
                    )
        else:
            unreal.MaterialEditingLibrary.set_material_instance_static_switch_parameter_value(
                material_instance,
                "use{}Texture".format("Diffuse"),
                True,
            )

    new_assets = [loaded_tex_list, material_instances, [loaded_imported_mesh]]
    for asset_list in new_assets:
        for asset in asset_list:
            asset_name_clean = asset.get_path_name().split(".")[0]
            unreal.EditorAssetLibrary.save_asset(asset_name_clean)


def import_static_mesh_publish_pipeline(
    identity: StaticMeshPublishIdentity,
    *,
    warn: WarnFn,
) -> Optional[str]:
    """Run mesh + textures + materials. Returns expected UE static-mesh object path."""
    imported_mesh, unreal_mesh_import_path = import_static_mesh(identity, warn=warn)
    if not imported_mesh:
        return None

    imported_textures = import_static_mesh_textures(
        identity, unreal_mesh_import_path, warn=warn
    )
    assign_setdec_static_mesh_materials(
        imported_mesh, unreal_mesh_import_path, imported_textures
    )
    return expected_ue_mesh_object_path_for_identity(identity)


def import_setdec_static_mesh_pipeline(
    asset_path: str,
    variant: str,
    version: str,
    *,
    warn: WarnFn,
) -> Optional[str]:
    identity = identity_from_legacy_setdec_args(asset_path, variant, version)
    return import_static_mesh_publish_pipeline(identity, warn=warn)


def ensure_static_mesh_imported(
    identity: StaticMeshPublishIdentity,
    *,
    warn: WarnFn,
) -> Optional[str]:
    """Return UE mesh object path, importing from publish disk when missing."""
    expected_path = expected_ue_mesh_object_path_for_identity(identity)
    if unreal.EditorAssetLibrary.load_asset(expected_path):
        return expected_path

    if _published_fbx_path_for_identity(identity, warn=warn) is None:
        return None

    import_static_mesh_publish_pipeline(identity, warn=warn)
    if unreal.EditorAssetLibrary.load_asset(expected_path):
        return expected_path
    return None


def ensure_setdec_static_mesh_imported(
    asset_path: str,
    variant: str,
    version: str,
    *,
    warn: WarnFn,
) -> Optional[str]:
    identity = identity_from_legacy_setdec_args(asset_path, variant, version)
    return ensure_static_mesh_imported(identity, warn=warn)

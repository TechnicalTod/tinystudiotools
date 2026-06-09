"""Maya static-mesh publish bundle (Set Dec + Asset Manager model).

All Maya/pymel imports are lazy. Callers outside Maya should not import this
module at package import time.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

USD_PREVIEW_PARAMETER_LIST = {
    "USDPreviewMaterial": {
        "diffuse": {"suffix": "Diffuse", "mayaParameter": "diffuseColor"},
        "emissive": {"suffix": "Emissive", "mayaParameter": "emissiveColor"},
        "ao": {"suffix": "AO", "mayaParameter": "occlusion"},
        "opacity": {"suffix": "Transparency", "mayaParameter": "opacity"},
        "metallic": {"suffix": "Metallic", "mayaParameter": "metallic"},
        "roughness": {"suffix": "Roughness", "mayaParameter": "roughness"},
        "normal": {"suffix": "Normal", "mayaParameter": "normal"},
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


def _create_directory(path: str | Path) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def publish_textures(
    mesh_object,
    bundle_root: str | Path,
    *,
    parameter_list=None,
) -> Tuple[List, str, dict]:
    """Copy and rewire USD Preview textures into ``{bundle_root}/tex/``."""
    import pymel.core as pm

    bundle_root = Path(bundle_root)
    parameter_list = parameter_list or USD_PREVIEW_PARAMETER_LIST

    shader_list: list = []
    shape_node = mesh_object.getShape()
    shading_groups = shape_node.shadingGroups()
    object_shaders = pm.ls(pm.listConnections(shading_groups), materials=True)
    for shader in object_shaders:
        shader_list.append(shader)

    pub_texturedict: dict = {}
    usd_params = parameter_list.get("USDPreviewMaterial")

    for shader in set(shader_list):
        pub_texturedict[shader] = {}
        for parameter in usd_params:
            try:
                maya_parameter_name = usd_params.get(parameter).get("mayaParameter")
                file_node = pm.listConnections(
                    f"{shader}.{maya_parameter_name}",
                    source=True,
                    destination=False,
                )
                if parameter == "normal" and file_node:
                    file_node = pm.listConnections(
                        file_node[0], source=True, destination=False
                    )
                if file_node:
                    texture_path = file_node[0].fileTextureName.get()
                    texture_path = texture_path.replace("\\", "/")
                    file_name = texture_path.split("/")[-1]
                    file_name_split = file_name.split(".<UDIM>.png")[0]
                    texture_dir = texture_path.split(file_name)[0]
                    texture_list = [
                        os.path.join(texture_dir, tex)
                        for tex in os.listdir(texture_dir)
                        if tex.endswith(".png") and file_name_split in tex
                    ]
                    pub_texturedict[shader][parameter] = texture_list
                else:
                    pub_texturedict[shader][parameter] = []
            except Exception:
                pub_texturedict[shader][parameter] = []

    texture_base_path = bundle_root / "tex"
    _create_directory(texture_base_path)

    for shader in pub_texturedict:
        for parameter_name in pub_texturedict[shader]:
            texture_list = pub_texturedict[shader][parameter_name]
            maya_parameter_name = usd_params.get(parameter_name).get("mayaParameter")
            for texture_path in texture_list:
                shutil.copy(texture_path, texture_base_path)
                file_node = pm.listConnections(f"{shader}.{maya_parameter_name}")
                if parameter_name == "normal" and file_node:
                    file_node = pm.listConnections(
                        file_node[0], source=True, destination=False
                    )
                texture_path = file_node[0].fileTextureName.get()
                texture_path = texture_path.replace("\\", "/")
                texture_name_full = texture_path.split("/")[-1]
                if texture_path.endswith(".<UDIM>.png"):
                    texture_name_no_udim = texture_name_full.split(".")[0]
                    new_texture_path_full = (
                        texture_base_path / f"{texture_name_no_udim}.1001.png"
                    )
                else:
                    new_texture_path_full = texture_base_path / texture_name_full
                file_node[0].fileTextureName.set(str(new_texture_path_full).replace("\\", "/"))

    return shader_list, str(texture_base_path).replace("\\", "/") + "/", pub_texturedict


def publish_geometry_bundle(
    mesh_object,
    bundle_root: str | Path,
    *,
    file_stem: str,
    asset_name: str,
    variant_name: str,
    version_label: str,
    base_path: str,
    existing_shaders: Sequence,
    usd_parent_scope: Optional[str] = None,
    publish_layout: Optional[str] = None,
    replace_in_scene: bool = True,
) -> List[str]:
    """Export fbx/usd/maya bundle and optionally replace the live mesh."""
    import pymel.core as pm

    bundle_root = Path(bundle_root)
    fbx_dir = bundle_root / "fbx"
    usd_dir = bundle_root / "usd"
    maya_dir = bundle_root / "maya"
    for directory in (fbx_dir, usd_dir, maya_dir):
        _create_directory(directory)

    fbx_path = fbx_dir / f"{file_stem}.fbx"
    usd_path = usd_dir / f"{file_stem}.usda"
    maya_path = maya_dir / f"{file_stem}.ma"

    original_parent = mesh_object.getParent()
    original_matrix = mesh_object.getMatrix(worldSpace=True)
    pm.parent(mesh_object, world=True)
    mesh_object.setMatrix(pm.dt.Matrix(), worldSpace=True)

    mesh_object.useOutlinerColor.set(True)
    mesh_object.outlinerColor.set([0, 0.6, 1])

    _ensure_string_attr(mesh_object, "assetName", asset_name)
    _ensure_string_attr(mesh_object, "variantName", variant_name)
    _ensure_string_attr(mesh_object, "version", version_label)
    _ensure_string_attr(mesh_object, "basePath", base_path.rstrip("/") + "/")
    _ensure_bool_attr(mesh_object, "published", True)
    _ensure_string_attr(
        mesh_object,
        "publishedShaderList",
        ",".join(str(shader) for shader in existing_shaders),
    )
    if publish_layout:
        _ensure_string_attr(mesh_object, "publishLayout", publish_layout)

    for shader in existing_shaders:
        shader_object = pm.PyNode(shader)
        _ensure_string_attr(shader_object, "shaderName", str(shader))

    scope = usd_parent_scope or asset_name
    pm.select(mesh_object)
    pm.mel.FBXResetExport()
    pm.mel.FBXExportSmoothingGroups(v=True)
    pm.mel.FBXExport(file=str(fbx_path).replace("\\", "/"), s=True)
    usd_export_options = f"parentScope={scope};materialsScopeName=mtl"
    pm.exportSelected(
        str(usd_path).replace("\\", "/"),
        force=True,
        type="USD export",
        options=usd_export_options,
    )
    pm.exportSelected(
        str(maya_path).replace("\\", "/"),
        force=True,
        type="mayaAscii",
        options="v=0;",
    )

    if replace_in_scene:
        pm.delete(mesh_object)
        imported_nodes = pm.importFile(
            str(maya_path),
            returnNewNodes=True,
            mergeNamespacesOnClash=False,
        )
        imported_transform = next(
            node for node in imported_nodes if isinstance(node, pm.nt.Transform)
        )
        if original_parent:
            pm.parent(imported_transform, original_parent)
        imported_transform.setMatrix(original_matrix, worldSpace=True)

    artifacts = [
        f"fbx/{fbx_path.name}",
        f"usd/{usd_path.name}",
        f"maya/{maya_path.name}",
    ]
    tex_dir = bundle_root / "tex"
    if tex_dir.is_dir() and any(tex_dir.iterdir()):
        artifacts.append("tex/")
    return artifacts


def publish_static_mesh_bundle(
    mesh_object,
    bundle_root: str | Path,
    *,
    file_stem: str,
    asset_name: str,
    variant_name: str,
    version_label: str,
    base_path: str,
    usd_parent_scope: Optional[str] = None,
    publish_layout: Optional[str] = None,
    replace_in_scene: bool = True,
) -> List[str]:
    """Full publish: textures + geometry bundle inside an undo chunk."""
    import pymel.core as pm

    pm.undoInfo(openChunk=True)
    try:
        existing_shaders, _, _ = publish_textures(mesh_object, bundle_root)
        artifacts = publish_geometry_bundle(
            mesh_object,
            bundle_root,
            file_stem=file_stem,
            asset_name=asset_name,
            variant_name=variant_name,
            version_label=version_label,
            base_path=base_path,
            existing_shaders=existing_shaders,
            usd_parent_scope=usd_parent_scope,
            publish_layout=publish_layout,
            replace_in_scene=replace_in_scene,
        )
    except Exception:
        pm.undoInfo(closeChunk=True)
        pm.undo()
        raise
    else:
        pm.undoInfo(closeChunk=True)
        return artifacts


def _ensure_string_attr(node, long_name: str, value: str) -> None:
    import pymel.core as pm

    if not node.hasAttr(long_name):
        pm.addAttr(node, longName=long_name, dataType="string", k=True)
    node.attr(long_name).set(value)


def _ensure_bool_attr(node, long_name: str, value: bool) -> None:
    import pymel.core as pm

    if not node.hasAttr(long_name):
        pm.addAttr(node, longName=long_name, attributeType="bool", k=True)
    node.attr(long_name).set(value)

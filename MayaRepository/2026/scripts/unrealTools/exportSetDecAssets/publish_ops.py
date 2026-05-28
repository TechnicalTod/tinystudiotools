import os
import shutil

import pymel.core as pm

from .constants import PARAMETER_LIST


def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print("Directory '{}' created.".format(path))
    else:
        print("Directory '{}' already exists.".format(path))


def publish_set_dec_textures(
    set_dec_object,
    set_dec_asset_path,
):
    shader_list = []
    set_dec_object_shape_node = set_dec_object.getShape()
    get_shading_groups = set_dec_object_shape_node.shadingGroups()
    set_dec_object_shaders = pm.ls(pm.listConnections(get_shading_groups), materials=True)
    print(set_dec_object_shaders)
    for shader in set_dec_object_shaders:
        shader_list.append(shader)

    pub_texturedict = {}
    usd_params = PARAMETER_LIST.get("USDPreviewMaterial")

    for shader in set(shader_list):
        pub_texturedict[shader] = {}
        for parameter in usd_params:
            try:
                maya_parameter_name = usd_params.get(parameter).get("mayaParameter")
                file_node = pm.listConnections(
                    "{}.{}".format(shader, maya_parameter_name), source=True, destination=False
                )

                if parameter == "normal":
                    file_node = pm.listConnections(file_node[0], source=True, destination=False)
                    print("NORMAL", file_node)
                if file_node:
                    print("ATANDARD", file_node)
                    texture_path = file_node[0].fileTextureName.get()
                    texture_path = texture_path.replace("\\", "/")
                    file_name = texture_path.split("/")[-1]
                    file_name_split = file_name.split(".<UDIM>.png")[0]
                    texture_path = texture_path.split(file_name)[0]
                    texture_list = [
                        os.path.join(texture_path, tex)
                        for tex in os.listdir(texture_path)
                        if tex.endswith(".png") and file_name_split in tex
                    ]
                    pub_texturedict[shader][parameter] = texture_list
                else:
                    pub_texturedict[shader][parameter] = []
            except Exception as e:
                print("No texture found for {}: {}".format(parameter, e))

    texture_base_path = set_dec_asset_path + "tex"
    create_directory(texture_base_path)

    for shader in pub_texturedict:
        print(shader)
        for parameter_name in pub_texturedict[shader]:
            print(parameter_name)
            texture_list = pub_texturedict[shader][parameter_name]
            maya_parameter_name = usd_params.get(parameter_name).get("mayaParameter")
            for texture_path in texture_list:
                shutil.copy(texture_path, texture_base_path)
                file_node = pm.listConnections("{}.{}".format(shader, maya_parameter_name))
                if parameter_name == "normal":
                    file_node = pm.listConnections(file_node[0], source=True, destination=False)
                texture_path = file_node[0].fileTextureName.get()
                texture_path = texture_path.replace("\\", "/")
                texture_name_full = texture_path.split("/")[-1]
                if texture_path.endswith(".<UDIM>.png"):
                    print("found UDIM tag")
                    texture_name_no_udim = texture_name_full.split(".")[0]
                    texture_name_add_udim_tag = texture_name_no_udim + ".1001.png"
                    new_texture_path_full = texture_base_path + "/" + texture_name_add_udim_tag
                    print(new_texture_path_full)
                    file_node[0].fileTextureName.set(new_texture_path_full)
                else:
                    print("no UDIM tag")
                    new_texture_path_full = texture_base_path + "/" + texture_name_full
                    print(new_texture_path_full)
                    file_node[0].fileTextureName.set(new_texture_path_full)

    return shader_list, texture_base_path, pub_texturedict


def publish_set_dec(
    set_dec_object,
    split_set_dec_object_name,
    set_dec_variant_name,
    set_dec_new_version,
    existing_shaders,
    set_dec_group_folder_name,
):
    set_dec_asset_path = (
        set_dec_group_folder_name
        + split_set_dec_object_name
        + "/"
        + set_dec_variant_name
        + "/"
        + set_dec_new_version
        + "/"
    )

    fbx_base_path = set_dec_asset_path + "fbx"
    fbx_file_name = "{}_{}.fbx".format(split_set_dec_object_name, set_dec_new_version)
    fbx_full_path = fbx_base_path + "/" + fbx_file_name
    usd_base_path = set_dec_asset_path + "usd"
    usd_file_name = "{}_{}.usda".format(split_set_dec_object_name, set_dec_new_version)
    usd_full_path = usd_base_path + "/" + usd_file_name
    maya_base_path = set_dec_asset_path + "maya"
    maya_file_name = "{}_{}.ma".format(split_set_dec_object_name, set_dec_new_version)
    maya_full_path = maya_base_path + "/" + maya_file_name

    new_dir_list = (fbx_base_path, usd_base_path, maya_base_path)

    for dir_path in new_dir_list:
        create_directory(dir_path)

    original_parent = set_dec_object.getParent()
    original_matrix = set_dec_object.getMatrix(worldSpace=True)
    pm.parent(set_dec_object, world=True)
    set_dec_object.setMatrix(pm.dt.Matrix(), worldSpace=True)

    set_dec_object.useOutlinerColor.set(True)
    set_dec_object.outlinerColor.set([0, 0.6, 1])

    pm.addAttr(set_dec_object, longName="assetName", dataType="string", k=True)
    set_dec_object.assetName.set(split_set_dec_object_name)
    pm.addAttr(set_dec_object, longName="variantName", dataType="string", k=True)
    set_dec_object.variantName.set(set_dec_variant_name)
    pm.addAttr(set_dec_object, longName="version", dataType="string", k=True)
    set_dec_object.version.set(set_dec_new_version)
    pm.addAttr(set_dec_object, longName="basePath", dataType="string", k=True)
    set_dec_object.basePath.set(set_dec_group_folder_name)
    pm.addAttr(set_dec_object, longName="published", attributeType="bool", k=True)
    set_dec_object.published.set(True)
    pm.addAttr(set_dec_object, longName="publishedShaderList", dataType="string", k=True)
    set_dec_object.publishedShaderList.set(",".join(str(i) for i in existing_shaders))

    for shader in existing_shaders:
        shader_object = pm.PyNode(shader)

        if not shader_object.hasAttr("shaderName"):
            pm.addAttr(shader_object, longName="shaderName", dataType="string", k=True)
        shader_object.shaderName.set(shader)

    pm.select(set_dec_object)
    pm.mel.FBXResetExport()
    pm.mel.FBXExportSmoothingGroups(v=True)
    pm.mel.FBXExport(file=fbx_full_path, s=True)
    usd_export_options = "parentScope={};materialsScopeName=mtl".format(split_set_dec_object_name)
    pm.exportSelected(usd_full_path, force=True, type="USD export", options=usd_export_options)
    pm.exportSelected(maya_full_path, force=True, type="mayaAscii", options="v=0;")

    pm.delete(set_dec_object)

    imported_nodes = pm.importFile(
        maya_full_path, returnNewNodes=True, mergeNamespacesOnClash=False
    )
    imported_transform = [node for node in imported_nodes if isinstance(node, pm.nt.Transform)][0]
    if original_parent:
        pm.parent(imported_transform, original_parent)
    imported_transform.setMatrix(original_matrix, worldSpace=True)

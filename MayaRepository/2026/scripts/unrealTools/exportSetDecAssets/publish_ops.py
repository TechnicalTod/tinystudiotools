"""Set Dec publish operations — thin wrapper around shared Maya publish ops."""

from __future__ import annotations

from genTools import static_mesh_publish_ops as _ops

from .constants import PARAMETER_LIST


def create_directory(path):
    _ops._create_directory(path)


def publish_set_dec_textures(set_dec_object, set_dec_asset_path):
    return _ops.publish_textures(
        set_dec_object,
        set_dec_asset_path,
        parameter_list=PARAMETER_LIST,
    )


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
    file_stem = f"{split_set_dec_object_name}_{set_dec_new_version}"
    _ops.publish_geometry_bundle(
        set_dec_object,
        set_dec_asset_path,
        file_stem=file_stem,
        asset_name=split_set_dec_object_name,
        variant_name=set_dec_variant_name,
        version_label=set_dec_new_version,
        base_path=set_dec_group_folder_name,
        existing_shaders=existing_shaders,
        usd_parent_scope=split_set_dec_object_name,
        publish_layout="setdec",
        replace_in_scene=True,
    )

"""Skeletal mesh publish path resolution."""

from __future__ import annotations

import os

from assetTools.setdec_paths import normalize_disk_path

from ..publish_layout import asset_manager_category_from_root, rig_unreal_root


def resolve_skeletal_publish_paths(
    asset_path: str,
    variant_name: str,
    version_number: str,
    *,
    layout: str,
) -> tuple[str, str, str]:
    """Return ``(fbx_dir, tex_dir, ue_import_dir)`` for one skeletal publish."""
    asset_path = normalize_disk_path(asset_path.rstrip("/\\"))
    asset_name = os.path.basename(asset_path)

    if layout == "rig_unreal":
        version_dir = normalize_disk_path(
            os.path.join(rig_unreal_root(asset_path), version_number)
        )
        category = (asset_manager_category_from_root(asset_path) or "chr").upper()
        ue_import_dir = "/Game/01_Assets/{}/{}/{}/{}".format(
            category,
            asset_name,
            variant_name,
            version_number,
        )
        return f"{version_dir}/", f"{version_dir}/tex/", ue_import_dir

    publish_dir = asset_path.split("/")[-4]
    ue_import_dir = "/Game/01_Assets/{}/{}/{}/{}".format(
        publish_dir,
        asset_name,
        variant_name,
        version_number,
    )
    bundle_root = f"{asset_path}/{variant_name}/{version_number}/"
    return (
        f"{bundle_root}unrealExport/",
        f"{bundle_root}tex/",
        ue_import_dir,
    )

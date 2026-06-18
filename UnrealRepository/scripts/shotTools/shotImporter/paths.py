"""Unreal content path builders for shot import."""

from __future__ import annotations

import re

from .constants import (
    ANIMATION_SUBDIR,
    ASSETS_ROOT,
    CUSTOM_GEO_ALEMBIC_SUBDIR,
    CUSTOM_GEO_FBX_SUBDIR,
    CUSTOM_GEO_SETDEC_SUBDIR,
    CUSTOM_GEO_SUBDIR,
    EPISODES_ROOT,
    MEDIA_SUBDIR,
)
from .manifest import (
    EXPORT_FORMAT_ALEMBIC,
    EXPORT_FORMAT_FBX,
    CustomAnimatedGeometryItem,
    PuppetItem,
    ShotInfo,
)


def shot_version_dir(shot_info: ShotInfo) -> str:
    return "{}/{}/{}/{}/{}".format(
        EPISODES_ROOT,
        shot_info.episode,
        shot_info.sequence,
        shot_info.shot_number,
        shot_info.version,
    )


def animation_dir(shot_dir: str) -> str:
    return "{}/{}".format(shot_dir, ANIMATION_SUBDIR)


def media_dir(shot_dir: str) -> str:
    return "{}/{}".format(shot_dir, MEDIA_SUBDIR)


def custom_geo_dir(shot_dir: str) -> str:
    return "{}/{}".format(shot_dir, CUSTOM_GEO_SUBDIR)


def custom_geo_fbx_dir(shot_dir: str) -> str:
    return "{}/{}/{}".format(shot_dir, CUSTOM_GEO_SUBDIR, CUSTOM_GEO_FBX_SUBDIR)


def custom_geo_alembic_dir(shot_dir: str) -> str:
    return "{}/{}/{}".format(shot_dir, CUSTOM_GEO_SUBDIR, CUSTOM_GEO_ALEMBIC_SUBDIR)


def custom_geo_setdec_item_dir(shot_dir: str, item: CustomAnimatedGeometryItem) -> str:
    stem = safe_artifact_stem(item.name)
    if item.export_format == EXPORT_FORMAT_ALEMBIC:
        return "{}/{}/{}/{}".format(
            shot_dir,
            CUSTOM_GEO_SUBDIR,
            CUSTOM_GEO_SETDEC_SUBDIR,
            stem,
        )
    return "{}/{}/{}/{}".format(
        shot_dir,
        CUSTOM_GEO_SUBDIR,
        CUSTOM_GEO_SETDEC_SUBDIR,
        stem,
    )


def custom_geo_import_dir(shot_dir: str, item: CustomAnimatedGeometryItem) -> str:
    if item.is_set_dec or item.product_type == "setDecAnimated":
        return custom_geo_setdec_item_dir(shot_dir, item)
    if item.export_format == EXPORT_FORMAT_ALEMBIC:
        return custom_geo_alembic_dir(shot_dir)
    return custom_geo_fbx_dir(shot_dir)


def safe_artifact_stem(name: str) -> str:
    name = name.split("|")[-1]
    name = name.replace(":", "_")
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("_") or "publishItem"


def custom_geo_actor_label(member_name: str) -> str:
    """Match Maya publish duplicate name for sequencer FBX binding."""
    return "{}_customGeo".format(safe_artifact_stem(member_name))


def level_asset_path(shot_dir: str, shot: str, version: str) -> str:
    base_asset_name = "{}_{}".format(shot, version)
    return "{}/PL_{}".format(shot_dir, base_asset_name)


def sequence_asset_path(shot_dir: str, shot: str, version: str) -> str:
    base_asset_name = "{}_{}".format(shot, version)
    return "{}/LS_{}".format(shot_dir, base_asset_name)


def puppet_asset_dir(puppet: PuppetItem) -> str:
    return "{}/{}/{}/{}/{}/".format(
        ASSETS_ROOT,
        puppet.asset_type,
        puppet.asset_name,
        puppet.variant,
        puppet.version,
    )


def media_source_asset_path(shot_dir: str) -> str:
    path_parts = shot_dir.split("/")
    asset_name = "_".join(path_parts[-2:])
    return "{}/{}".format(media_dir(shot_dir), asset_name)

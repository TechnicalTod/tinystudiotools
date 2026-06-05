"""Unreal content path builders for shot import."""

from __future__ import annotations

from .constants import ANIMATION_SUBDIR, ASSETS_ROOT, EPISODES_ROOT, MEDIA_SUBDIR
from .manifest import PuppetItem, ShotInfo


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

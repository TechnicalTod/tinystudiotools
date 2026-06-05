from __future__ import annotations

import re
from pathlib import Path

from genTools.studio_python_path import ensure_gen_tools_shared

from .models import ShotInfo

ensure_gen_tools_shared()

try:
    from studioShowPaths import show_root_for
except ImportError:
    show_root_for = None


SCENE_DESCRIPTION_FOLDER = "sceneDescription"
SCENE_DESCRIPTION_STEM = "ShotDescription"
CUSTOM_GEO_SUBDIR = "customGeo"


def create_directory(path: Path) -> None:
    if not path.exists():
        path.mkdir(parents=True)
        print("Directory '{}' created.".format(path.as_posix()))
    else:
        print("Directory '{}' already exists.".format(path.as_posix()))


def _show_root(project: str) -> Path:
    if show_root_for is not None:
        try:
            return show_root_for(project)
        except RuntimeError:
            pass
    return Path("Y:/{}".format(project))


def episode_and_sequence(shot_number: str) -> tuple[str, str]:
    parts = shot_number.split("_")
    if len(parts) < 2:
        raise ValueError(
            "Shot number '{}' does not contain episode and sequence segments.".format(
                shot_number
            )
        )
    episode = parts[0]
    sequence = "{}_{}".format(parts[0], parts[1])
    return episode, sequence


def publish_root(shot_info: ShotInfo) -> Path:
    if not shot_info.project:
        raise ValueError("Shot project could not be resolved from the current scene.")
    if not shot_info.shot_number:
        raise ValueError("Shot number could not be resolved from the current scene.")
    if not shot_info.version:
        raise ValueError("Version could not be resolved from the current scene filename.")

    episode, sequence = episode_and_sequence(shot_info.shot_number)
    return (
        _show_root(shot_info.project)
        / "episodes"
        / episode
        / sequence
        / shot_info.shot_number
        / "publish"
        / "unreal"
        / SCENE_DESCRIPTION_FOLDER
        / shot_info.version
    )


def safe_artifact_stem(name: str, *, puppet: bool = False) -> str:
    if puppet:
        name = name.split(":")[0]
    name = name.split("|")[-1]
    name = name.replace(":", "_")
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("_") or "publishItem"


def artifact_path(
    shot_info: ShotInfo,
    item_name: str,
    extension: str,
    *,
    puppet: bool = False,
) -> Path:
    extension = extension if extension.startswith(".") else "." + extension
    root = publish_root(shot_info)
    create_directory(root)
    file_name = "{}_{}{}".format(
        safe_artifact_stem(item_name, puppet=puppet),
        shot_info.version,
        extension,
    )
    return root / file_name


def scene_description_path(shot_info: ShotInfo) -> Path:
    return artifact_path(shot_info, SCENE_DESCRIPTION_STEM, ".json")


def publish_root_string(shot_info: ShotInfo) -> str:
    return publish_root(shot_info).as_posix()


def custom_geo_dir(shot_info: ShotInfo) -> Path:
    root = publish_root(shot_info) / CUSTOM_GEO_SUBDIR
    create_directory(root)
    return root


def custom_geo_fbx_path(shot_info: ShotInfo, member_name: str) -> Path:
    file_name = "{}_{}.fbx".format(
        safe_artifact_stem(member_name),
        shot_info.version,
    )
    return custom_geo_dir(shot_info) / file_name


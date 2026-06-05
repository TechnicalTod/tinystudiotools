from __future__ import annotations

import os

import maya.cmds as mc
import maya.mel as mm
import pymel.core as pm

from .models import CameraPublishItem, PuppetPublishItem, ShotInfo, ShotPublishManifest


DEFAULT_CAMERAS = {"persp", "back", "front", "side", "top"}
PUPPET_ATTRS = (
    "assetType",
    "assetName",
    "variant",
    "version",
    "rootJointName",
    "visGeoGroupName",
)


def _attr_string(node, attr_name: str) -> str:
    try:
        value = node.attr(attr_name).get()
    except Exception:
        return ""
    return "" if value is None else str(value)


def _scene_path() -> str:
    try:
        return (mc.file(sceneName=True, q=True) or "").replace("\\", "/")
    except Exception:
        return ""


def _version_from_filename(scene_path: str) -> str:
    if not scene_path:
        return ""
    filename = scene_path.split("/")[-1]
    if "_" not in filename:
        return ""
    return filename.split("_")[-1].split(".")[0]


def _shot_parts_from_path(scene_path: str) -> tuple[str, str]:
    """Return (project, shot_number) from a path using the current show layout."""
    project = os.environ.get("SHOW_NAME", "").strip()
    shot_number = ""
    parts = [part for part in scene_path.replace("\\", "/").split("/") if part]

    if "episodes" in parts:
        episodes_index = parts.index("episodes")
        if episodes_index > 0 and not project:
            project = parts[episodes_index - 1]
        if len(parts) > episodes_index + 3:
            shot_number = parts[episodes_index + 3]

    if not project:
        try:
            project = parts[-9]
        except IndexError:
            project = ""
    if not shot_number:
        try:
            shot_number = parts[-5]
        except IndexError:
            shot_number = ""

    return project, shot_number


def collect_shot_info() -> ShotInfo:
    scene_path = _scene_path()
    project, shot_number = _shot_parts_from_path(scene_path)
    version = _version_from_filename(scene_path)

    if not scene_path or not shot_number:
        print("You are not in a saved shot scene")

    start_frame = pm.playbackOptions(query=True, min=True)
    end_frame = pm.playbackOptions(query=True, max=True)
    fps = mm.eval("currentTimeUnitToFPS()")

    return ShotInfo(
        project=project,
        shot_number=shot_number,
        version=version,
        timeline_start=start_frame,
        timeline_end=end_frame,
        fps=fps,
        scene_path=scene_path,
    )


def collect_cameras() -> list[CameraPublishItem]:
    cameras: list[CameraPublishItem] = []

    for camera_shape in pm.ls(type="camera", long=True):
        camera_transform = camera_shape.getParent()
        camera_name = camera_transform.name()
        if camera_transform.nodeName() in DEFAULT_CAMERAS:
            continue

        image_plate = ""
        image_planes = pm.listConnections(camera_shape, type="imagePlane") or []
        if image_planes:
            try:
                image_plate = pm.getAttr("{}.imageName".format(image_planes[0])) or ""
            except Exception:
                image_plate = ""

        cameras.append(
            CameraPublishItem(
                name=camera_name,
                focal_length=camera_shape.attr("focalLength").get(),
                horizontal_film_aperture=round(
                    camera_shape.attr("horizontalFilmAperture").get() * 25.4, 3
                ),
                vertical_film_aperture=round(
                    camera_shape.attr("verticalFilmAperture").get() * 25.4, 3
                ),
                image_plate=image_plate,
            )
        )

    return cameras


def collect_puppets() -> list[PuppetPublishItem]:
    puppets: list[PuppetPublishItem] = []
    puppet_nodes = [node for node in pm.ls(type="transform") if node.hasAttr("rootJointName")]

    for puppet in puppet_nodes:
        puppets.append(
            PuppetPublishItem(
                name=puppet.name(),
                asset_type=_attr_string(puppet, "assetType"),
                asset_name=_attr_string(puppet, "assetName"),
                variant=_attr_string(puppet, "variant"),
                version=_attr_string(puppet, "version"),
                root_joint_name=_attr_string(puppet, "rootJointName"),
                vis_geo_group_name=_attr_string(puppet, "visGeoGroupName"),
            )
        )

    return puppets


def build_manifest() -> ShotPublishManifest:
    return ShotPublishManifest(
        shot_info=collect_shot_info(),
        cameras=collect_cameras(),
        puppets=collect_puppets(),
        extra_info={"notes": "N/A"},
    )


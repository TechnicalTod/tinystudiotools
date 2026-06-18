from __future__ import annotations

import os

import maya.cmds as mc
import maya.mel as mm
import pymel.core as pm

from .classification import (
    export_format_for_source_set,
    is_published_setdec_from_attrs,
    partial_setdec_warning,
    product_type_for_item,
)
from .custom_geo_sets import list_custom_animated_geometry_members
from .models import (
    CameraPublishItem,
    CustomAnimatedGeometryItem,
    PuppetPublishItem,
    ShotInfo,
    ShotPublishManifest,
)
from .paths import resolve_custom_animated_geometry_paths, safe_artifact_stem


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


def _attr_bool(node, attr_name: str) -> bool:
    try:
        return bool(node.attr(attr_name).get())
    except Exception:
        return False


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


def _is_animated_transform(node, start_frame: float, end_frame: float) -> bool:
    del start_frame, end_frame
    attrs = ("translateX", "translateY", "translateZ", "rotateX", "rotateY", "rotateZ")
    for attr_name in attrs:
        try:
            attr = node.attr(attr_name)
            key_count = pm.keyframe(attr, query=True, keyframeCount=True) or 0
            if key_count > 0:
                return True
            connections = pm.listConnections(attr, type="animCurve") or []
            if connections:
                return True
        except Exception:
            continue
    return False


def _setdec_attrs_for_node(node) -> dict[str, object]:
    attrs = {"name": node.name()}
    attrs["published"] = _attr_bool(node, "published")
    attrs["assetName"] = _attr_string(node, "assetName")
    attrs["basePath"] = _attr_string(node, "basePath")
    attrs["variantName"] = _attr_string(node, "variantName")
    attrs["version"] = _attr_string(node, "version")
    attrs["publishLayout"] = _attr_string(node, "publishLayout")
    return attrs


def _has_obvious_deformers(node) -> bool:
    deformers = pm.listHistory(node, pruneDagObjects=True) or []
    for deformer in deformers:
        node_type = pm.nodeType(deformer)
        if node_type in {
            "skinCluster",
            "blendShape",
            "wrap",
            "cluster",
            "lattice",
            "nonLinear",
            "deltaMush",
            "tension",
        }:
            return True
    return False


def _duplicate_short_name_warnings(items: list[CustomAnimatedGeometryItem]) -> list[str]:
    warnings: list[str] = []
    seen: dict[tuple[str, str], str] = {}
    for item in items:
        short_name = safe_artifact_stem(item.name)
        bucket = (item.source_set, short_name)
        if bucket in seen:
            warnings.append(
                "Duplicate short name '{}' in set '{}' for '{}' and '{}'.".format(
                    short_name,
                    item.source_set,
                    seen[bucket],
                    item.name,
                )
            )
        else:
            seen[bucket] = item.name
    return warnings


def collect_custom_animated_geometry(
    shot_info: ShotInfo | None = None,
) -> tuple[list[CustomAnimatedGeometryItem], list[str]]:
    members = list_custom_animated_geometry_members()
    if not members:
        return [], []

    start_frame = pm.playbackOptions(query=True, min=True)
    end_frame = pm.playbackOptions(query=True, max=True)
    items: list[CustomAnimatedGeometryItem] = []
    warnings: list[str] = []

    for source_set, member_name in members:
        if not pm.objExists(member_name):
            continue
        node = pm.PyNode(member_name)
        attrs = _setdec_attrs_for_node(node)
        is_set_dec = is_published_setdec_from_attrs(attrs)
        partial_warning = partial_setdec_warning(attrs)
        if partial_warning:
            warnings.append(partial_warning)

        export_format = export_format_for_source_set(source_set)
        product_type = product_type_for_item(
            export_format=export_format,
            is_set_dec=is_set_dec,
        )
        animated = _is_animated_transform(node, start_frame, end_frame)
        has_deformers = _has_obvious_deformers(node)

        if export_format == "fbx" and has_deformers:
            warnings.append(
                "FBX-set member '{}' has deformers; verify transform-only export is intended.".format(
                    member_name
                )
            )
        if export_format == "alembic" and not has_deformers and not animated:
            warnings.append(
                "Alembic-set member '{}' has no obvious deformers or transform animation.".format(
                    member_name
                )
            )

        item = CustomAnimatedGeometryItem(
            name=member_name,
            product_type=product_type,
            export_format=export_format,
            source_set=source_set,
            animated=animated,
            is_set_dec=is_set_dec,
        )
        if is_set_dec:
            item.asset_name = str(attrs.get("assetName") or "")
            item.base_path = str(attrs.get("basePath") or "")
            item.variant = str(attrs.get("variantName") or "")
            item.asset_version = str(attrs.get("version") or "")
            item.publish_layout = str(attrs.get("publishLayout") or "")
        items.append(item)

    warnings.extend(_duplicate_short_name_warnings(items))
    if shot_info is not None:
        resolve_custom_animated_geometry_paths(shot_info, items)
    return items, warnings


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
    shot_info = collect_shot_info()
    custom_items, warnings = collect_custom_animated_geometry(shot_info)
    return ShotPublishManifest(
        shot_info=shot_info,
        cameras=collect_cameras(),
        puppets=collect_puppets(),
        custom_animated_geometry=custom_items,
        extra_info={"notes": "N/A"},
        warnings=warnings,
    )

from __future__ import annotations

import json
from pathlib import Path

import pymel.core as pm

from . import paths
from .models import (
    CameraPublishItem,
    CustomGeoItem,
    PuppetPublishItem,
    ShotPublishManifest,
)


def _delete_node(node) -> None:
    if node is None:
        return
    try:
        if pm.objExists(node):
            pm.delete(node)
    except Exception:
        pass


def _bake_nodes(nodes, start_frame: float, end_frame: float) -> None:
    pm.bakeResults(
        nodes,
        simulation=True,
        t=(start_frame, end_frame),
        sampleBy=1,
        oversamplingRate=1,
        disableImplicitControl=True,
        preserveOutsideKeys=True,
        sparseAnimCurveBake=False,
        removeBakedAttributeFromLayer=False,
        bakeOnOverrideLayer=False,
        minimizeRotation=True,
        controlPoints=False,
        shape=True,
    )


def _export_selected_fbx(export_path: Path) -> None:
    pm.mel.FBXResetExport()
    pm.mel.FBXExportSmoothingGroups(v=True)
    pm.mel.FBXExport(file=export_path.as_posix(), s=True)


def publish_camera(
    camera: CameraPublishItem,
    manifest: ShotPublishManifest,
) -> CameraPublishItem:
    duplicated_camera = None
    export_path = paths.artifact_path(
        manifest.shot_info,
        camera.name,
        ".fbx",
    )
    camera.export_path = export_path.as_posix()

    try:
        duplicated_camera = pm.duplicate(
            camera.name,
            name=paths.safe_artifact_stem(camera.name) + "_UECam",
            un=True,
            ic=True,
        )[0]
        _bake_nodes(
            duplicated_camera,
            manifest.shot_info.timeline_start,
            manifest.shot_info.timeline_end,
        )
        pm.parent(duplicated_camera, world=True)
        pm.select(duplicated_camera, replace=True)
        _export_selected_fbx(export_path)
        camera.publish_status = "published"
        camera.error = ""
    except Exception as exc:
        camera.publish_status = "failed"
        camera.error = str(exc)
        raise
    finally:
        _delete_node(duplicated_camera)

    return camera


def _matching_duplicate_root(duplicated_puppet, root_joint_name: str):
    root_short_name = root_joint_name.split("|")[-1].split(":")[-1]
    joints = pm.listRelatives(duplicated_puppet, allDescendents=True, type="joint") or []

    for joint in joints:
        node_name = joint.nodeName()
        if (
            joint.name() == root_joint_name
            or node_name == root_joint_name
            or node_name.split(":")[-1] == root_short_name
        ):
            return joint

    raise RuntimeError(
        "Could not find duplicated root joint '{}' under '{}'.".format(
            root_joint_name,
            duplicated_puppet,
        )
    )


def publish_puppet(
    puppet: PuppetPublishItem,
    manifest: ShotPublishManifest,
) -> PuppetPublishItem:
    duplicated_puppet = None
    export_root_joint = None
    export_path = paths.artifact_path(
        manifest.shot_info,
        puppet.name,
        ".fbx",
        puppet=True,
    )
    puppet.export_path = export_path.as_posix()

    try:
        duplicated_puppet = pm.duplicate(
            puppet.name,
            name=paths.safe_artifact_stem(puppet.name, puppet=True) + "_puppetExport",
            un=True,
            ic=True,
        )[0]
        export_root_joint = _matching_duplicate_root(
            duplicated_puppet,
            puppet.root_joint_name,
        )
        all_joints = pm.listRelatives(
            export_root_joint,
            allDescendents=True,
            type="joint",
        ) or []
        all_joints.append(export_root_joint)

        _bake_nodes(
            all_joints,
            manifest.shot_info.timeline_start,
            manifest.shot_info.timeline_end,
        )
        pm.parent(export_root_joint, world=True)
        _delete_node(duplicated_puppet)
        duplicated_puppet = None

        pm.select(export_root_joint, replace=True)
        _export_selected_fbx(export_path)
        puppet.publish_status = "published"
        puppet.error = ""
    except Exception as exc:
        puppet.publish_status = "failed"
        puppet.error = str(exc)
        raise
    finally:
        _delete_node(export_root_joint)
        _delete_node(duplicated_puppet)

    return puppet


def _hierarchy_nodes(root) -> list:
    nodes = [root]
    descendants = pm.listRelatives(root, allDescendents=True) or []
    nodes.extend(descendants)
    return nodes


def publish_custom_geo_item(
    item: CustomGeoItem,
    manifest: ShotPublishManifest,
) -> CustomGeoItem:
    duplicated_geo = None
    export_path = paths.custom_geo_fbx_path(manifest.shot_info, item.name)
    item.export_path = export_path.as_posix()

    try:
        duplicated_geo = pm.duplicate(
            item.name,
            name=paths.safe_artifact_stem(item.name) + "_customGeo",
            un=True,
            ic=True,
        )[0]
        if item.animated:
            _bake_nodes(
                _hierarchy_nodes(duplicated_geo),
                manifest.shot_info.timeline_start,
                manifest.shot_info.timeline_end,
            )
        pm.parent(duplicated_geo, world=True)
        pm.select(duplicated_geo, replace=True)
        _export_selected_fbx(export_path)
        item.publish_status = "published"
        item.error = ""
    except Exception as exc:
        item.publish_status = "failed"
        item.error = str(exc)
        raise
    finally:
        _delete_node(duplicated_geo)

    return item


def publish_custom_geo_items(manifest: ShotPublishManifest) -> None:
    for item in manifest.custom_geo:
        try:
            publish_custom_geo_item(item, manifest)
        except Exception as exc:
            print("Failed to publish custom geo '{}': {}".format(item.name, exc))


def write_manifest(manifest: ShotPublishManifest) -> Path:
    out_path = paths.scene_description_path(manifest.shot_info)
    with open(out_path, "w", encoding="utf-8") as json_file:
        json.dump(manifest.to_dict(), json_file, indent=4)
    return out_path


def publish_manifest(manifest: ShotPublishManifest) -> Path:
    for camera in manifest.cameras:
        try:
            publish_camera(camera, manifest)
        except Exception as exc:
            print("Failed to publish camera '{}': {}".format(camera.name, exc))

    for puppet in manifest.puppets:
        try:
            publish_puppet(puppet, manifest)
        except Exception as exc:
            print("Failed to publish puppet '{}': {}".format(puppet.name, exc))

    publish_custom_geo_items(manifest)

    return write_manifest(manifest)


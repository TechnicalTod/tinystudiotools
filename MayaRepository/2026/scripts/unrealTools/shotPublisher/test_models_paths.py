from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from unrealTools.shotPublisher import paths
from unrealTools.shotPublisher.models import (
    CameraPublishItem,
    CustomGeoItem,
    PuppetPublishItem,
    ShotInfo,
    ShotPublishManifest,
)


class ShotPublisherModelPathTests(unittest.TestCase):
    def test_manifest_serializes_structured_publish_data(self):
        manifest = ShotPublishManifest(
            shot_info=ShotInfo(
                project="TestShow",
                shot_number="ep001_sq010_sh020",
                version="v003",
                timeline_start=1001,
                timeline_end=1050,
                fps=24,
                scene_path="Y:/TestShow/episodes/ep001/ep001_sq010/ep001_sq010_sh020/work/maya/layout/test_v003.ma",
            ),
            cameras=[
                CameraPublishItem(
                    name="renderCam",
                    focal_length=35,
                    horizontal_film_aperture=36,
                    vertical_film_aperture=20.25,
                    image_plate="plate.exr",
                    export_path="renderCam_v003.fbx",
                    publish_status="published",
                )
            ],
            puppets=[
                PuppetPublishItem(
                    name="charA:puppet",
                    asset_type="CHR",
                    asset_name="CharA",
                    variant="rig_Main",
                    version="v012",
                    root_joint_name="root_joint",
                    vis_geo_group_name="visGeo",
                )
            ],
        )

        data = manifest.to_dict()

        self.assertEqual(data["schemaVersion"], 2)
        self.assertEqual(data["shotInfo"]["shotNumber"], "ep001_sq010_sh020")
        self.assertEqual(data["cameras"][0]["exportPath"], "renderCam_v003.fbx")
        self.assertEqual(data["puppets"][0]["rootJointName"], "root_joint")

    def test_manifest_serializes_custom_geo_items(self):
        manifest = ShotPublishManifest(
            shot_info=ShotInfo(
                project="TestShow",
                shot_number="ep001_sq010_sh020",
                version="v003",
            ),
            custom_geo=[
                CustomGeoItem(
                    name="propA",
                    animated=True,
                    export_path="Y:/TestShow/customGeo/propA_v003.fbx",
                    publish_status="published",
                ),
                CustomGeoItem(
                    name="groupB",
                    animated=False,
                    export_path="Y:/TestShow/customGeo/groupB_v003.fbx",
                    publish_status="published",
                ),
            ],
        )

        data = manifest.to_dict()

        self.assertEqual(data["schemaVersion"], 2)
        self.assertEqual(data["customGeo"]["setName"], "unreal_custom_geo")
        self.assertEqual(len(data["customGeo"]["items"]), 2)
        self.assertTrue(data["customGeo"]["items"][0]["animated"])
        self.assertFalse(data["customGeo"]["items"][1]["animated"])

    def test_custom_geo_fbx_path_uses_custom_geo_subdir(self):
        info = ShotInfo(
            project="TestShow",
            shot_number="ep001_sq010_sh020",
            version="v003",
        )
        old_base = os.environ.get("TINYSTUDIO_BASE_SHOW_DIR")
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                os.environ["TINYSTUDIO_BASE_SHOW_DIR"] = tmp_dir
                fbx_path = paths.custom_geo_fbx_path(info, "propA")

                expected = (
                    Path(tmp_dir)
                    / "TestShow"
                    / "episodes"
                    / "ep001"
                    / "ep001_sq010"
                    / "ep001_sq010_sh020"
                    / "publish"
                    / "unreal"
                    / "sceneDescription"
                    / "v003"
                    / "customGeo"
                    / "propA_v003.fbx"
                )
                self.assertEqual(fbx_path, expected)
        finally:
            if old_base is None:
                os.environ.pop("TINYSTUDIO_BASE_SHOW_DIR", None)
            else:
                os.environ["TINYSTUDIO_BASE_SHOW_DIR"] = old_base

    def test_publish_root_uses_show_environment_layout(self):
        old_base = os.environ.get("TINYSTUDIO_BASE_SHOW_DIR")
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                os.environ["TINYSTUDIO_BASE_SHOW_DIR"] = tmp_dir
                info = ShotInfo(
                    project="TestShow",
                    shot_number="ep001_sq010_sh020",
                    version="v003",
                )

                root = paths.publish_root(info)

                expected = (
                    Path(tmp_dir)
                    / "TestShow"
                    / "episodes"
                    / "ep001"
                    / "ep001_sq010"
                    / "ep001_sq010_sh020"
                    / "publish"
                    / "unreal"
                    / "sceneDescription"
                    / "v003"
                )
                self.assertEqual(root, expected)
        finally:
            if old_base is None:
                os.environ.pop("TINYSTUDIO_BASE_SHOW_DIR", None)
            else:
                os.environ["TINYSTUDIO_BASE_SHOW_DIR"] = old_base


if __name__ == "__main__":
    unittest.main()


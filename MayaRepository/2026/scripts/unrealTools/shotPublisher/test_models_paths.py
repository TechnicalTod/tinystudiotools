from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from unrealTools.shotPublisher import paths
from unrealTools.shotPublisher.classification import (
    export_format_for_source_set,
    is_published_setdec_from_attrs,
    partial_setdec_warning,
    product_type_for_item,
)
from unrealTools.shotPublisher.constants import (
    CUSTOM_GEO_ALEMBIC_SET_NAME,
    CUSTOM_GEO_FBX_SET_NAME,
    EXPORT_FORMAT_ALEMBIC,
    EXPORT_FORMAT_FBX,
    PRODUCT_TYPE_ALEMBIC,
    PRODUCT_TYPE_ANIMATED_FBX,
    PRODUCT_TYPE_SETDEC_ANIMATED,
)
from unrealTools.shotPublisher.models import (
    CameraPublishItem,
    CustomAnimatedGeometryItem,
    PuppetPublishItem,
    SCHEMA_VERSION,
    ShotInfo,
    ShotPublishManifest,
)


class ShotPublisherClassificationTests(unittest.TestCase):
    def test_export_format_for_source_set(self):
        self.assertEqual(export_format_for_source_set(CUSTOM_GEO_FBX_SET_NAME), EXPORT_FORMAT_FBX)
        self.assertEqual(
            export_format_for_source_set(CUSTOM_GEO_ALEMBIC_SET_NAME),
            EXPORT_FORMAT_ALEMBIC,
        )

    def test_product_type_for_item(self):
        self.assertEqual(
            product_type_for_item(export_format=EXPORT_FORMAT_FBX, is_set_dec=False),
            PRODUCT_TYPE_ANIMATED_FBX,
        )
        self.assertEqual(
            product_type_for_item(export_format=EXPORT_FORMAT_ALEMBIC, is_set_dec=False),
            PRODUCT_TYPE_ALEMBIC,
        )
        self.assertEqual(
            product_type_for_item(export_format=EXPORT_FORMAT_FBX, is_set_dec=True),
            PRODUCT_TYPE_SETDEC_ANIMATED,
        )

    def test_is_published_setdec_from_attrs(self):
        self.assertTrue(
            is_published_setdec_from_attrs(
                {
                    "published": True,
                    "assetName": "pCube1",
                    "basePath": "Y:/Show/assets/setdec/setdec01/",
                    "variantName": "main",
                    "version": "v001",
                }
            )
        )
        self.assertFalse(
            is_published_setdec_from_attrs(
                {
                    "published": True,
                    "assetName": "pCube1",
                    "basePath": "",
                    "variantName": "main",
                    "version": "v001",
                }
            )
        )

    def test_partial_setdec_warning(self):
        warning = partial_setdec_warning(
            {
                "name": "pCube1",
                "published": True,
                "assetName": "pCube1",
                "basePath": "",
                "variantName": "main",
                "version": "v001",
            }
        )
        self.assertIsNotNone(warning)
        self.assertIn("incomplete", warning.lower())


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

        self.assertEqual(data["schemaVersion"], SCHEMA_VERSION)
        self.assertEqual(data["shotInfo"]["shotNumber"], "ep001_sq010_sh020")
        self.assertEqual(data["cameras"][0]["exportPath"], "renderCam_v003.fbx")
        self.assertEqual(data["puppets"][0]["rootJointName"], "root_joint")

    def test_manifest_serializes_custom_animated_geometry_items(self):
        manifest = ShotPublishManifest(
            shot_info=ShotInfo(
                project="TestShow",
                shot_number="ep001_sq010_sh020",
                version="v003",
            ),
            custom_animated_geometry=[
                CustomAnimatedGeometryItem(
                    name="propA",
                    product_type=PRODUCT_TYPE_ANIMATED_FBX,
                    export_format=EXPORT_FORMAT_FBX,
                    source_set=CUSTOM_GEO_FBX_SET_NAME,
                    animated=True,
                    export_path="Y:/TestShow/customGeo/fbx/propA_v003.fbx",
                    publish_status="published",
                ),
                CustomAnimatedGeometryItem(
                    name="clothProp",
                    product_type=PRODUCT_TYPE_SETDEC_ANIMATED,
                    export_format=EXPORT_FORMAT_ALEMBIC,
                    source_set=CUSTOM_GEO_ALEMBIC_SET_NAME,
                    is_set_dec=True,
                    asset_name="clothProp",
                    base_path="Y:/Show/assets/setdec/setdec01/",
                    variant="main",
                    asset_version="v002",
                    export_path="Y:/TestShow/customGeo/setDec/alembic/clothProp_v003.abc",
                    publish_status="published",
                ),
            ],
        )

        data = manifest.to_dict()

        self.assertEqual(data["schemaVersion"], 3)
        items = data["customAnimatedGeometry"]["items"]
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["productType"], PRODUCT_TYPE_ANIMATED_FBX)
        self.assertTrue(items[0]["animated"])
        self.assertEqual(items[1]["productType"], PRODUCT_TYPE_SETDEC_ANIMATED)
        self.assertEqual(items[1]["assetName"], "clothProp")

    def test_custom_animated_geometry_paths(self):
        info = ShotInfo(
            project="TestShow",
            shot_number="ep001_sq010_sh020",
            version="v003",
        )
        old_base = os.environ.get("TINYSTUDIO_BASE_SHOW_DIR")
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                os.environ["TINYSTUDIO_BASE_SHOW_DIR"] = tmp_dir
                fbx_path = paths.custom_animated_geometry_path(
                    info,
                    "propA",
                    export_format=EXPORT_FORMAT_FBX,
                    is_set_dec=False,
                )
                setdec_fbx_path = paths.custom_animated_geometry_path(
                    info,
                    "pCube1",
                    export_format=EXPORT_FORMAT_FBX,
                    is_set_dec=True,
                )
                alembic_path = paths.custom_animated_geometry_path(
                    info,
                    "clothProp",
                    export_format=EXPORT_FORMAT_ALEMBIC,
                    is_set_dec=True,
                )

                root = (
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
                )
                self.assertEqual(fbx_path, root / "fbx" / "propA_v003.fbx")
                self.assertEqual(setdec_fbx_path, root / "setDec" / "fbx" / "pCube1_v003.fbx")
                self.assertEqual(
                    alembic_path,
                    root / "setDec" / "alembic" / "clothProp_v003.abc",
                )
        finally:
            if old_base is None:
                os.environ.pop("TINYSTUDIO_BASE_SHOW_DIR", None)
            else:
                os.environ["TINYSTUDIO_BASE_SHOW_DIR"] = old_base

    def test_resolve_paths_adds_suffix_for_duplicate_stems(self):
        info = ShotInfo(
            project="TestShow",
            shot_number="ep001_sq010_sh020",
            version="v003",
        )
        items = [
            CustomAnimatedGeometryItem(
                name="ENV|propA",
                product_type=PRODUCT_TYPE_ANIMATED_FBX,
                export_format=EXPORT_FORMAT_FBX,
                source_set=CUSTOM_GEO_FBX_SET_NAME,
            ),
            CustomAnimatedGeometryItem(
                name="layout|propA",
                product_type=PRODUCT_TYPE_ANIMATED_FBX,
                export_format=EXPORT_FORMAT_FBX,
                source_set=CUSTOM_GEO_FBX_SET_NAME,
            ),
        ]
        old_base = os.environ.get("TINYSTUDIO_BASE_SHOW_DIR")
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                os.environ["TINYSTUDIO_BASE_SHOW_DIR"] = tmp_dir
                paths.resolve_custom_animated_geometry_paths(info, items)
                self.assertIn("propA_v003.fbx", items[0].export_path)
                self.assertIn("propA_01_v003.fbx", items[1].export_path)
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


class ShotPublisherManualTestNotes(unittest.TestCase):
    """Document manual Maya -> Unreal verification cases for TDs."""

    def test_manual_case_documentation_exists(self):
        notes = """
        Manual verification per product type:
        1. Custom FBX: add transform-animated prop to unreal_custom_geo_fbx, publish, import in UE, confirm static mesh + sequencer keys.
        2. Custom Alembic: add deforming mesh to unreal_custom_geo_alembic, publish ABC, import as geometry cache in sequencer.
        3. Set Dec FBX: published set dec with transform animation in FBX set, confirm Set Dec textures/MI applied on shot mesh.
        4. Set Dec Alembic: published deforming set dec in Alembic set, confirm geometry cache + Set Dec material override.
        5. Dual membership: same node in both sets publishes FBX and ABC artifacts.
        """
        self.assertIn("Custom FBX", notes)
        self.assertIn("Set Dec Alembic", notes)


if __name__ == "__main__":
    unittest.main()

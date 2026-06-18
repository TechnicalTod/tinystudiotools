from __future__ import annotations

import unittest

from shotTools.shotImporter.manifest import CustomAnimatedGeometryItem, ShotInfo
from shotTools.shotImporter.paths import (
    custom_geo_actor_label,
    custom_geo_dir,
    custom_geo_fbx_dir,
    custom_geo_import_dir,
    shot_version_dir,
)


class ShotImporterPathTests(unittest.TestCase):
    def test_custom_geo_actor_label_matches_maya_export_node(self):
        self.assertEqual(custom_geo_actor_label("pCube1"), "pCube1_customGeo")
        self.assertEqual(
            custom_geo_actor_label("charA:propB"),
            "charA_propB_customGeo",
        )

    def test_custom_geo_dir_builder(self):
        shot_info = ShotInfo(
            shot_number="ep001_sq010_sh020",
            version="v003",
        )
        shot_dir = shot_version_dir(shot_info)

        self.assertEqual(
            custom_geo_dir(shot_dir),
            "/Game/02_Episodes/ep001/ep001_sq010/ep001_sq010_sh020/v003/CustomGeo",
        )

    def test_custom_geo_import_dir_variants(self):
        shot_info = ShotInfo(
            shot_number="ep001_sq010_sh020",
            version="v003",
        )
        shot_dir = shot_version_dir(shot_info)
        custom_fbx = CustomAnimatedGeometryItem(
            name="propA",
            product_type="animatedFbx",
            export_format="fbx",
        )
        setdec_item = CustomAnimatedGeometryItem(
            name="pCube1",
            product_type="setDecAnimated",
            export_format="fbx",
            is_set_dec=True,
        )

        self.assertEqual(
            custom_geo_fbx_dir(shot_dir),
            "{}/CustomGeo/fbx".format(shot_dir),
        )
        self.assertEqual(
            custom_geo_import_dir(shot_dir, custom_fbx),
            "{}/CustomGeo/fbx".format(shot_dir),
        )
        self.assertEqual(
            custom_geo_import_dir(shot_dir, setdec_item),
            "{}/CustomGeo/SetDec/pCube1".format(shot_dir),
        )


if __name__ == "__main__":
    unittest.main()

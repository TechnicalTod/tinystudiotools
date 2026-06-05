from __future__ import annotations

import unittest

from shotTools.shotImporter.manifest import ShotInfo
from shotTools.shotImporter.paths import (
    custom_geo_actor_label,
    custom_geo_dir,
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


if __name__ == "__main__":
    unittest.main()

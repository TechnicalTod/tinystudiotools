from __future__ import annotations

import unittest

from shotTools.shotImporter.manifest import parse_shot_manifest


class ShotManifestParserTests(unittest.TestCase):
    def test_parses_schema_v1_manifest(self):
        data = {
            "schemaVersion": 1,
            "shotInfo": {
                "project": "TestShow",
                "shotNumber": "ep001_sq010_sh020",
                "version": "v003",
                "timeline": {"startFrame": 1001, "endFrame": 1050},
                "fps": 24,
            },
            "cameras": [
                {
                    "name": "renderCam",
                    "exportPath": "Y:/TestShow/renderCam_v003.fbx",
                    "horizontalFilmAperture": 36.0,
                    "verticalFilmAperture": 20.25,
                    "imagePlate": "",
                }
            ],
            "puppets": [
                {
                    "name": "charA:puppet",
                    "exportPath": "Y:/TestShow/charA_v003.fbx",
                    "assetType": "CHR",
                    "assetName": "CharA",
                    "variant": "rig_Main",
                    "version": "v012",
                }
            ],
        }

        manifest = parse_shot_manifest(data)

        self.assertEqual(manifest.shot_info.shot_number, "ep001_sq010_sh020")
        self.assertEqual(manifest.shot_info.version, "v003")
        self.assertEqual(manifest.shot_info.playback_end_frame, 1051)
        self.assertEqual(manifest.cameras[0].export_path, "Y:/TestShow/renderCam_v003.fbx")
        self.assertEqual(manifest.puppets[0].asset_name, "CharA")

    def test_rejects_legacy_list_format(self):
        with self.assertRaises(ValueError):
            parse_shot_manifest([{"Cameras": []}, {"Puppets": []}, {"Shot Info": []}])


if __name__ == "__main__":
    unittest.main()

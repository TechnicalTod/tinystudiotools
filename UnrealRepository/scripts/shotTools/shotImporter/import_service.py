"""Orchestrate shot import from a published scene description JSON."""

from __future__ import annotations

import traceback
from dataclasses import dataclass, field

import unreal

from . import camera_ops, custom_geo_ops, puppet_ops
from .manifest import ShotManifest, load_manifest
from .setup_ops import ShotSetupResult, create_shot_setup


@dataclass
class ImportResult:
    success: bool
    manifest: ShotManifest | None = None
    setup: ShotSetupResult | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def save_assets(asset_paths: list[str]) -> None:
    for asset_path in asset_paths:
        asset_name_clean = str(asset_path).split(".")[0]
        unreal.EditorAssetLibrary.save_asset(asset_name_clean)


def import_shot_from_json(json_path: str) -> ImportResult:
    result = ImportResult(success=False)

    try:
        manifest = load_manifest(json_path)
        result.manifest = manifest
        result.warnings.extend(manifest.warnings)
    except Exception as exc:
        result.errors.append("Failed to read shot scene description: {}".format(exc))
        traceback.print_exc()
        return result

    try:
        setup = create_shot_setup(manifest.shot_info)
        result.setup = setup
    except Exception as exc:
        result.errors.append("Shot setup failed: {}".format(exc))
        traceback.print_exc()
        return result

    if manifest.cameras:
        try:
            camera_ops.import_cameras(setup, manifest.cameras)
        except Exception as exc:
            message = "Camera import failed: {}".format(exc)
            result.errors.append(message)
            traceback.print_exc()
    else:
        result.warnings.append("No cameras found in published json")

    if manifest.puppets:
        try:
            puppet_ops.import_puppets(setup, manifest.puppets)
        except Exception as exc:
            message = "Puppet import failed: {}".format(exc)
            result.errors.append(message)
            traceback.print_exc()
    else:
        result.warnings.append("No puppets found in published json")

    if manifest.custom_animated_geometry:
        try:
            custom_geo_ops.import_custom_animated_geometry_items(
                setup,
                manifest.custom_animated_geometry,
                warn=result.warnings.append,
            )
        except Exception as exc:
            message = "Custom animated geometry import failed: {}".format(exc)
            result.errors.append(message)
            traceback.print_exc()

    save_assets([setup.level_asset_path, setup.sequence_asset_path])
    result.success = not result.errors
    return result

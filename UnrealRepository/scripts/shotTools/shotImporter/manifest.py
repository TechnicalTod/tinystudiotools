"""Parse Maya shot scene description JSON for Unreal import.

Expects the structured manifest written by ``unrealTools.shotPublisher``
(schemaVersion 1, 2, or 3).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


SCHEMA_VERSION = 3

PRODUCT_TYPE_ANIMATED_FBX = "animatedFbx"
PRODUCT_TYPE_ALEMBIC = "alembic"
PRODUCT_TYPE_SETDEC_ANIMATED = "setDecAnimated"

EXPORT_FORMAT_FBX = "fbx"
EXPORT_FORMAT_ALEMBIC = "alembic"


@dataclass
class ShotInfo:
    shot_number: str = ""
    version: str = ""
    start_frame: float = 0.0
    end_frame: float = 0.0
    fps: float = 24.0
    project: str = ""

    @property
    def episode(self) -> str:
        return self.shot_number.split("_")[0] if self.shot_number else ""

    @property
    def sequence(self) -> str:
        parts = self.shot_number.split("_")
        if len(parts) < 2:
            return ""
        return "{}_{}".format(parts[0], parts[1])

    @property
    def playback_end_frame(self) -> float:
        return self.end_frame + 1


@dataclass
class CameraItem:
    name: str
    export_path: str = ""
    horizontal_film_aperture: float = 0.0
    vertical_film_aperture: float = 0.0
    image_plate: str = ""


@dataclass
class PuppetItem:
    name: str
    export_path: str = ""
    asset_type: str = ""
    asset_name: str = ""
    variant: str = ""
    version: str = ""


@dataclass
class CustomAnimatedGeometryItem:
    name: str
    export_path: str = ""
    product_type: str = PRODUCT_TYPE_ANIMATED_FBX
    export_format: str = EXPORT_FORMAT_FBX
    source_set: str = ""
    animated: bool = False
    is_set_dec: bool = False
    asset_name: str = ""
    base_path: str = ""
    variant: str = ""
    asset_version: str = ""
    publish_layout: str = ""
    publish_status: str = "published"
    error: str = ""


@dataclass
class ShotManifest:
    shot_info: ShotInfo
    schema_version: int = SCHEMA_VERSION
    cameras: list[CameraItem] = field(default_factory=list)
    puppets: list[PuppetItem] = field(default_factory=list)
    custom_animated_geometry: list[CustomAnimatedGeometryItem] = field(
        default_factory=list
    )
    warnings: list[str] = field(default_factory=list)

    @property
    def custom_geo(self) -> list[CustomAnimatedGeometryItem]:
        """Backward-compatible alias for older import code."""
        return self.custom_animated_geometry


def _field(data: dict[str, Any], key: str, default: Any = "") -> Any:
    value = data.get(key, default)
    return default if value is None else value


def _parse_shot_info(shot_info: dict[str, Any]) -> ShotInfo:
    timeline = shot_info.get("timeline") or {}
    return ShotInfo(
        project=str(_field(shot_info, "project", default="")),
        shot_number=str(_field(shot_info, "shotNumber", default="")),
        version=str(_field(shot_info, "version", default="")),
        start_frame=float(_field(timeline, "startFrame", default=0)),
        end_frame=float(_field(timeline, "endFrame", default=0)),
        fps=float(_field(shot_info, "fps", default=24)),
    )


def _parse_camera(entry: dict[str, Any]) -> CameraItem:
    return CameraItem(
        name=str(_field(entry, "name", default="")),
        export_path=str(_field(entry, "exportPath", default="")),
        horizontal_film_aperture=float(_field(entry, "horizontalFilmAperture", default=0)),
        vertical_film_aperture=float(_field(entry, "verticalFilmAperture", default=0)),
        image_plate=str(_field(entry, "imagePlate", default="")),
    )


def _parse_puppet(entry: dict[str, Any]) -> PuppetItem:
    return PuppetItem(
        name=str(_field(entry, "name", default="")),
        export_path=str(_field(entry, "exportPath", default="")),
        asset_type=str(_field(entry, "assetType", default="")),
        asset_name=str(_field(entry, "assetName", default="")),
        variant=str(_field(entry, "variant", default="")),
        version=str(_field(entry, "version", default="")),
    )


def _parse_custom_animated_geometry_item(entry: dict[str, Any]) -> CustomAnimatedGeometryItem:
    product_type = str(_field(entry, "productType", default=PRODUCT_TYPE_ANIMATED_FBX))
    export_format = str(_field(entry, "exportFormat", default=""))
    if not export_format:
        if product_type == PRODUCT_TYPE_ALEMBIC:
            export_format = EXPORT_FORMAT_ALEMBIC
        elif product_type == PRODUCT_TYPE_SETDEC_ANIMATED:
            export_format = EXPORT_FORMAT_FBX
        else:
            export_format = EXPORT_FORMAT_FBX

    is_set_dec = bool(_field(entry, "isSetDec", default=False))
    if product_type == PRODUCT_TYPE_SETDEC_ANIMATED:
        is_set_dec = True

    return CustomAnimatedGeometryItem(
        name=str(_field(entry, "name", default="")),
        export_path=str(_field(entry, "exportPath", default="")),
        product_type=product_type,
        export_format=export_format,
        source_set=str(_field(entry, "sourceSet", default="")),
        animated=bool(_field(entry, "animated", default=False)),
        is_set_dec=is_set_dec,
        asset_name=str(_field(entry, "assetName", default="")),
        base_path=str(_field(entry, "basePath", default="")),
        variant=str(_field(entry, "variant", default="")),
        asset_version=str(_field(entry, "version", default="")),
        publish_layout=str(_field(entry, "publishLayout", default="")),
        publish_status=str(_field(entry, "publishStatus", default="published")),
        error=str(_field(entry, "error", default="")),
    )


def _parse_v2_custom_geo_items(items: list[Any]) -> list[CustomAnimatedGeometryItem]:
    parsed: list[CustomAnimatedGeometryItem] = []
    for entry in items:
        if not isinstance(entry, dict):
            continue
        parsed.append(
            CustomAnimatedGeometryItem(
                name=str(_field(entry, "name", default="")),
                export_path=str(_field(entry, "exportPath", default="")),
                product_type=PRODUCT_TYPE_ANIMATED_FBX,
                export_format=EXPORT_FORMAT_FBX,
                animated=bool(_field(entry, "animated", default=False)),
                publish_status=str(_field(entry, "publishStatus", default="published")),
                error=str(_field(entry, "error", default="")),
            )
        )
    return parsed


def parse_shot_manifest(data: Any) -> ShotManifest:
    """Return a normalized manifest from a schemaVersion 1, 2, or 3 JSON object."""
    if not isinstance(data, dict) or "shotInfo" not in data:
        raise ValueError(
            "Unrecognized shot scene description format. "
            "Expected schemaVersion 1, 2, or 3 manifest with shotInfo."
        )

    schema_version = int(_field(data, "schemaVersion", default=1))
    custom_items: list[CustomAnimatedGeometryItem] = []

    if schema_version >= 3:
        block = data.get("customAnimatedGeometry") or {}
        custom_items = [
            _parse_custom_animated_geometry_item(entry)
            for entry in block.get("items") or []
            if isinstance(entry, dict)
        ]
    else:
        custom_geo_block = data.get("customGeo") or {}
        custom_items = _parse_v2_custom_geo_items(custom_geo_block.get("items") or [])

    warnings = [str(w) for w in data.get("warnings") or []]

    return ShotManifest(
        shot_info=_parse_shot_info(data.get("shotInfo") or {}),
        schema_version=schema_version,
        cameras=[_parse_camera(entry) for entry in data.get("cameras") or []],
        puppets=[_parse_puppet(entry) for entry in data.get("puppets") or []],
        custom_animated_geometry=custom_items,
        warnings=warnings,
    )


def load_manifest(json_path: str) -> ShotManifest:
    with open(json_path, "r", encoding="utf-8") as file:
        return parse_shot_manifest(json.load(file))

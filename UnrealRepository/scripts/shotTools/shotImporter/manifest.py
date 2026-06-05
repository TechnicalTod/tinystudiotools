"""Parse Maya shot scene description JSON for Unreal import.

Expects the structured manifest written by ``unrealTools.shotPublisher``
(schemaVersion 1 or 2).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


SCHEMA_VERSION = 2


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
class CustomGeoItem:
    name: str
    export_path: str = ""
    animated: bool = False


@dataclass
class ShotManifest:
    shot_info: ShotInfo
    cameras: list[CameraItem] = field(default_factory=list)
    puppets: list[PuppetItem] = field(default_factory=list)
    custom_geo: list[CustomGeoItem] = field(default_factory=list)


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


def _parse_custom_geo_item(entry: dict[str, Any]) -> CustomGeoItem:
    return CustomGeoItem(
        name=str(_field(entry, "name", default="")),
        export_path=str(_field(entry, "exportPath", default="")),
        animated=bool(_field(entry, "animated", default=False)),
    )


def parse_shot_manifest(data: Any) -> ShotManifest:
    """Return a normalized manifest from a schemaVersion 1 or 2 JSON object."""
    if not isinstance(data, dict) or "shotInfo" not in data:
        raise ValueError(
            "Unrecognized shot scene description format. "
            "Expected schemaVersion 1 or 2 manifest with shotInfo, cameras, and puppets."
        )

    custom_geo_block = data.get("customGeo") or {}
    custom_geo_items = custom_geo_block.get("items") or []

    return ShotManifest(
        shot_info=_parse_shot_info(data.get("shotInfo") or {}),
        cameras=[_parse_camera(entry) for entry in data.get("cameras") or []],
        puppets=[_parse_puppet(entry) for entry in data.get("puppets") or []],
        custom_geo=[_parse_custom_geo_item(entry) for entry in custom_geo_items],
    )


def load_manifest(json_path: str) -> ShotManifest:
    with open(json_path, "r", encoding="utf-8") as file:
        return parse_shot_manifest(json.load(file))

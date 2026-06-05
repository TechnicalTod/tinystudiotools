from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


SCHEMA_VERSION = 2


@dataclass
class ShotInfo:
    project: str = ""
    shot_number: str = ""
    version: str = ""
    timeline_start: float = 0.0
    timeline_end: float = 0.0
    fps: float = 0.0
    scene_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "shotNumber": self.shot_number,
            "version": self.version,
            "timeline": {
                "startFrame": self.timeline_start,
                "endFrame": self.timeline_end,
            },
            "fps": self.fps,
            "scenePath": self.scene_path,
        }

    def display_rows(self) -> list[tuple[str, Any]]:
        return [
            ("Project", self.project),
            ("Shot Number", self.shot_number),
            ("Version", self.version),
            (
                "Timeline",
                {
                    "Start Frame": self.timeline_start,
                    "End Frame": self.timeline_end,
                },
            ),
            ("FPS", self.fps),
        ]


@dataclass
class PublishItem:
    name: str
    export_path: str = ""
    publish_status: str = "pending"
    error: str = ""

    def publish_fields(self) -> dict[str, str]:
        data: dict[str, str] = {}
        if self.export_path:
            data["exportPath"] = self.export_path
        if self.publish_status:
            data["publishStatus"] = self.publish_status
        if self.error:
            data["error"] = self.error
        return data


@dataclass
class CameraPublishItem(PublishItem):
    focal_length: float = 0.0
    horizontal_film_aperture: float = 0.0
    vertical_film_aperture: float = 0.0
    image_plate: str = ""

    def attributes(self) -> dict[str, Any]:
        data = {
            "focalLength": self.focal_length,
            "horizontalFilmAperture": self.horizontal_film_aperture,
            "verticalFilmAperture": self.vertical_film_aperture,
            "imagePlate": self.image_plate,
        }
        data.update(self.publish_fields())
        return data

    def to_dict(self) -> dict[str, Any]:
        data = {"name": self.name}
        data.update(self.attributes())
        return data


@dataclass
class PuppetPublishItem(PublishItem):
    asset_type: str = ""
    asset_name: str = ""
    variant: str = ""
    version: str = ""
    root_joint_name: str = ""
    vis_geo_group_name: str = ""

    def attributes(self) -> dict[str, Any]:
        data = {
            "assetType": self.asset_type,
            "assetName": self.asset_name,
            "variant": self.variant,
            "version": self.version,
            "rootJointName": self.root_joint_name,
            "visGeoGroupName": self.vis_geo_group_name,
        }
        data.update(self.publish_fields())
        return data

    def to_dict(self) -> dict[str, Any]:
        data = {"name": self.name}
        data.update(self.attributes())
        return data


@dataclass
class CustomGeoItem(PublishItem):
    animated: bool = False

    def attributes(self) -> dict[str, Any]:
        data = {"animated": self.animated}
        data.update(self.publish_fields())
        return data

    def to_dict(self) -> dict[str, Any]:
        data = {"name": self.name}
        data.update(self.attributes())
        return data


@dataclass
class ShotPublishManifest:
    shot_info: ShotInfo
    cameras: list[CameraPublishItem] = field(default_factory=list)
    puppets: list[PuppetPublishItem] = field(default_factory=list)
    custom_geo: list[CustomGeoItem] = field(default_factory=list)
    extra_info: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        from .constants import CUSTOM_GEO_SET_NAME

        data = {
            "schemaVersion": SCHEMA_VERSION,
            "shotInfo": self.shot_info.to_dict(),
            "cameras": [camera.to_dict() for camera in self.cameras],
            "puppets": [puppet.to_dict() for puppet in self.puppets],
            "extraInfo": self.extra_info,
            "warnings": self.warnings,
        }
        if self.custom_geo:
            data["customGeo"] = {
                "setName": CUSTOM_GEO_SET_NAME,
                "items": [item.to_dict() for item in self.custom_geo],
            }
        return data

    def remove_camera(self, name: str) -> None:
        self.cameras = [camera for camera in self.cameras if camera.name != name]

    def remove_puppet(self, name: str) -> None:
        self.puppets = [puppet for puppet in self.puppets if puppet.name != name]

    def remove_custom_geo(self, name: str) -> None:
        self.custom_geo = [item for item in self.custom_geo if item.name != name]

    def clear_publish_items(self) -> None:
        self.cameras = []
        self.puppets = []
        self.custom_geo = []


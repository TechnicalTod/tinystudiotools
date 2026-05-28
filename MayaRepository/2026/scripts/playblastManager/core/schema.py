"""Load playblast_schema.json."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List


_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "configs" / "playblast_schema.json"


@dataclass(frozen=True)
class PlayblastSchema:
    schema_version: int
    version_padding: int
    frame_padding: int
    default_frame_source: str
    default_show_ornaments: bool
    default_display_mode: str
    default_quality: int
    display_modes: List[str]


def load_schema(path: Path | None = None) -> PlayblastSchema:
    config_path = path or _SCHEMA_PATH
    data = json.loads(config_path.read_text(encoding="utf-8"))
    output = data.get("output", {})
    defaults = data.get("defaults", {})
    return PlayblastSchema(
        schema_version=int(data.get("schemaVersion", 1)),
        version_padding=int(output.get("version_padding", 3)),
        frame_padding=int(output.get("frame_padding", 4)),
        default_frame_source=str(defaults.get("frame_source", "scene")),
        default_show_ornaments=bool(defaults.get("show_ornaments", True)),
        default_display_mode=str(defaults.get("display_mode", "smoothShaded")),
        default_quality=int(defaults.get("quality", 100)),
        display_modes=list(data.get("display_modes", ["smoothShaded"])),
    )

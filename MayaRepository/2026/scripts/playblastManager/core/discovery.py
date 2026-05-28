"""Scan playblast history on disk."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .path_parser import ShotContext

_VERSION_DIR_RE = re.compile(r"^v(?P<version>\d+)$", re.IGNORECASE)


@dataclass(frozen=True)
class RenderRecord:
    camera: str
    version: int
    directory: Path
    first_frame: Optional[Path]
    frame_count: int
    mtime: float

    @property
    def created_label(self) -> str:
        return datetime.fromtimestamp(self.mtime).strftime("%Y-%m-%d %H:%M")


def _first_png(directory: Path) -> Optional[Path]:
    pngs = sorted(directory.glob("*.png"))
    return pngs[0] if pngs else None


def list_renders(shot: ShotContext) -> List[RenderRecord]:
    """Return completed playblast renders for the shot, newest first."""
    root = shot.playblasts_root
    if not root.exists():
        return []

    records: list[RenderRecord] = []
    for camera_dir in sorted(root.iterdir()):
        if not camera_dir.is_dir():
            continue
        camera = camera_dir.name
        for version_dir in camera_dir.iterdir():
            if not version_dir.is_dir():
                continue
            match = _VERSION_DIR_RE.match(version_dir.name)
            if not match:
                continue
            version = int(match.group("version"))
            pngs = list(version_dir.glob("*.png"))
            mtime = version_dir.stat().st_mtime
            if pngs:
                mtime = max(p.stat().st_mtime for p in pngs)
            records.append(
                RenderRecord(
                    camera=camera,
                    version=version,
                    directory=version_dir,
                    first_frame=_first_png(version_dir),
                    frame_count=len(pngs),
                    mtime=mtime,
                )
            )

    records.sort(key=lambda r: (r.mtime, r.camera, r.version), reverse=True)
    return records

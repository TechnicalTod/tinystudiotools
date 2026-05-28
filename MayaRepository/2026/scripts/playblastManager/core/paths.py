"""Path builders for playblast output."""

from __future__ import annotations

from pathlib import Path

from .path_parser import ShotContext


def render_dir(shot: ShotContext, camera: str, version: int, *, padding: int = 3) -> Path:
    return shot.playblasts_root / camera / f"v{version:0{padding}d}"


def filename_base(shot: ShotContext, camera: str) -> str:
    return f"{shot.scene_basename}_{camera}"


def sequence_prefix(output_dir: Path, base: str, *, frame_padding: int = 4) -> str:
    """Maya playblast ``filename`` prefix with frame padding."""
    hashes = "#" * frame_padding
    return str((output_dir / f"{base}.{hashes}").as_posix())

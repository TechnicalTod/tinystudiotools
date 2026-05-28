"""Orchestrate playblast rendering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional

from ..host import CameraInfo, MayaHost
from .context import StudioContext
from .discovery import RenderRecord, list_renders
from .path_parser import ShotContext, validate_scene_for_render
from .paths import filename_base
from .schema import PlayblastSchema
from .versioning import VersionReservationError, reserve_version_dir


@dataclass(frozen=True)
class RenderSettings:
    start_frame: float
    end_frame: float
    show_ornaments: bool
    display_mode: str
    quality: int


class RenderValidationError(RuntimeError):
    """Scene or selection is not valid for rendering."""


def render(
    host: MayaHost,
    ctx: StudioContext,
    shot: ShotContext,
    cameras: List[CameraInfo],
    settings: RenderSettings,
    schema: PlayblastSchema,
    *,
    progress: Optional[Callable[[str], None]] = None,
) -> List[RenderRecord]:
    """Render PNG sequences for each camera. Returns new history records."""
    scene = host.current_scene_path()
    parsed_shot, error = validate_scene_for_render(
        scene,
        ctx,
        is_modified=host.is_modified(),
    )
    if parsed_shot is None or error:
        raise RenderValidationError(error or "Scene is not valid for rendering.")
    if parsed_shot.scene_path != shot.scene_path:
        shot = parsed_shot

    if not cameras:
        raise RenderValidationError("Select at least one camera to render.")

    new_records: list[RenderRecord] = []
    for cam in cameras:
        if progress:
            progress(f"Rendering {cam.shape}…")
        try:
            version_dir, version = reserve_version_dir(
                shot.playblasts_root,
                cam.shape,
                padding=schema.version_padding,
            )
        except VersionReservationError as exc:
            raise RenderValidationError(str(exc)) from exc

        base = filename_base(shot, cam.shape)
        frames = host.playblast(
            cam.shape,
            version_dir,
            base,
            settings.start_frame,
            settings.end_frame,
            cam.width,
            cam.height,
            show_ornaments=settings.show_ornaments,
            display_mode=settings.display_mode,
            quality=settings.quality,
            frame_padding=schema.frame_padding,
        )

        mtime = version_dir.stat().st_mtime
        first = frames[0] if frames else None
        if first:
            mtime = first.stat().st_mtime

        new_records.append(
            RenderRecord(
                camera=cam.shape,
                version=version,
                directory=version_dir,
                first_frame=first,
                frame_count=len(frames),
                mtime=mtime,
            )
        )

    return new_records

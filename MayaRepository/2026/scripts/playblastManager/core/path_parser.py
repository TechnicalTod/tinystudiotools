"""Reverse-parse an open Maya scene path into shot context."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .context import StudioContext


@dataclass(frozen=True)
class ShotContext:
    """Shot identity derived from the open scene file path."""

    show_root: Path
    episode: str
    sequence: str
    shot: str
    dcc: str
    scene_path: Path
    scene_basename: str

    @property
    def playblasts_root(self) -> Path:
        return (
            self.show_root
            / "episodes"
            / self.episode
            / self.sequence
            / self.shot
            / "work"
            / self.dcc
            / "playblasts"
        )

    @property
    def shot_label(self) -> str:
        return f"{self.episode} / {self.sequence} / {self.shot}"


def _is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def parse_shot_scene(scene: Path, ctx: StudioContext) -> Optional[ShotContext]:
    """Parse a scene path under ``<show_root>/episodes/...``.

    Accepts scenes directly under ``work/<dcc>/`` or under
    ``work/<dcc>/<task>/``.
    """
    if not scene or not scene.suffix:
        return None

    show_root = ctx.show_root
    scene = Path(str(scene).replace("\\", "/"))

    if not _is_under(scene, show_root):
        return None

    try:
        rel = scene.resolve().relative_to(show_root.resolve())
    except (OSError, ValueError):
        rel = scene.relative_to(show_root)

    parts = rel.parts
    if len(parts) < 7:
        return None
    if parts[0] != "episodes":
        return None

    episode, sequence, shot = parts[1], parts[2], parts[3]
    if parts[4] != "work":
        return None

    dcc = parts[5]
    if dcc != "maya":
        return None

    return ShotContext(
        show_root=show_root,
        episode=episode,
        sequence=sequence,
        shot=shot,
        dcc=dcc,
        scene_path=scene,
        scene_basename=scene.stem,
    )


def validate_scene_for_render(
    scene: Optional[Path],
    ctx: StudioContext,
    *,
    is_modified: bool,
) -> tuple[Optional[ShotContext], str]:
    """Return ``(shot, error_message)``. ``shot`` is set when render may proceed."""
    if scene is None or not str(scene).strip():
        return None, "Scene is untitled. Save under a valid shot path before rendering."

    scene = Path(str(scene).replace("\\", "/"))
    if is_modified:
        return None, "Scene has unsaved changes. Save the scene before rendering."

    shot = parse_shot_scene(scene, ctx)
    if shot is None:
        expected = (
            f"{ctx.show_root}/episodes/<episode>/<sequence>/<shot>/work/maya/[<task>/]<scene>.ma"
        )
        return None, f"Scene is not under a recognised shot path.\nExpected pattern:\n{expected}"

    return shot, ""

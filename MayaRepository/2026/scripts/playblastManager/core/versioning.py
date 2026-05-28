"""Per-camera playblast version discovery and atomic directory reservation."""

from __future__ import annotations

import re
from pathlib import Path


_VERSION_DIR_RE = re.compile(r"^v(?P<version>\d+)$", re.IGNORECASE)


class VersionReservationError(RuntimeError):
    """Raised when no free version directory can be reserved."""


def next_version(playblasts_root: Path, camera: str) -> int:
    """Return the next free version integer for ``camera`` (starts at 1)."""
    camera_root = playblasts_root / camera
    if not camera_root.exists():
        return 1

    versions: list[int] = []
    for child in camera_root.iterdir():
        if not child.is_dir():
            continue
        match = _VERSION_DIR_RE.match(child.name)
        if match:
            versions.append(int(match.group("version")))

    if not versions:
        return 1
    return max(versions) + 1


def reserve_version_dir(
    playblasts_root: Path,
    camera: str,
    *,
    padding: int = 3,
    max_attempts: int = 64,
) -> tuple[Path, int]:
    """Atomically reserve ``playblasts/<camera>/v###`` by creating the directory.

    Returns:
        ``(version_dir, version_number)``
    """
    playblasts_root.mkdir(parents=True, exist_ok=True)
    camera_root = playblasts_root / camera
    camera_root.mkdir(parents=True, exist_ok=True)

    candidate = next_version(playblasts_root, camera)
    for _ in range(max_attempts):
        version_dir = camera_root / f"v{candidate:0{padding}d}"
        try:
            version_dir.mkdir(exist_ok=False)
            return version_dir, candidate
        except FileExistsError:
            candidate += 1
            continue

    raise VersionReservationError(
        f"Could not reserve a version directory under {camera_root} after "
        f"{max_attempts} attempts."
    )

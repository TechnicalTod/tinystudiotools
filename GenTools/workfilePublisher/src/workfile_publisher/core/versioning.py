"""Workfile version scanning and atomic reservation.

The scheme is filename-based: existing files matching
``<prefix>_<task>_<variant>_v(\\d+).<ext>`` are scanned and the next free
integer is reserved by exclusively creating an empty placeholder file. The
host adapter then overwrites that placeholder with the real save, which is
the safest cross-platform way to avoid two artists colliding on ``v###``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass(frozen=True)
class WorkfileEntry:
    """One discovered workfile on disk."""

    path: Path
    asset_or_shot: str
    task: str
    variant: str
    version: int
    ext: str

    @property
    def filename(self) -> str:
        return self.path.name


def _filename_regex(prefix: str, task: str, variant: Optional[str], ext: str) -> re.Pattern[str]:
    """Build a regex that captures the version number for the given combo.

    ``variant=None`` matches any variant (used when listing all workfiles in a
    folder, e.g. for the UI table). When ``variant`` is provided we anchor it.
    """
    variant_pattern = r"(?P<variant>[a-z0-9][a-z0-9_-]*)" if variant is None else re.escape(variant)
    return re.compile(
        rf"^{re.escape(prefix)}_{re.escape(task)}_{variant_pattern}_v(?P<version>\d+)\.{re.escape(ext)}$",
        re.IGNORECASE,
    )


def list_workfiles(
    folder: Path,
    prefix: str,
    task: str,
    ext: str,
    variant: Optional[str] = None,
) -> List[WorkfileEntry]:
    """Return all matching workfiles in ``folder`` sorted version-descending.

    Folders that don't exist yield an empty list. Hidden / temp / placeholder
    files (zero bytes) are still returned because the UI may want to surface
    them; callers can filter on size if needed.
    """
    if not folder.exists():
        return []

    pattern = _filename_regex(prefix, task, variant, ext)
    entries: List[WorkfileEntry] = []
    for child in folder.iterdir():
        if not child.is_file():
            continue
        match = pattern.match(child.name)
        if not match:
            continue
        if variant is None:
            this_variant = match.group("variant")
        else:
            this_variant = variant
        entries.append(
            WorkfileEntry(
                path=child,
                asset_or_shot=prefix,
                task=task,
                variant=this_variant,
                version=int(match.group("version")),
                ext=ext,
            )
        )

    entries.sort(key=lambda e: (e.variant, e.version), reverse=True)
    return entries


def next_version(
    folder: Path,
    prefix: str,
    task: str,
    variant: str,
    ext: str,
) -> int:
    """Return the next free version integer (starting at 1)."""
    existing = list_workfiles(folder, prefix, task, ext, variant=variant)
    if not existing:
        return 1
    return max(entry.version for entry in existing) + 1


class VersionReservationError(RuntimeError):
    """Raised when no free version slot can be reserved."""


def reserve_next_version(
    folder: Path,
    prefix: str,
    task: str,
    variant: str,
    ext: str,
    *,
    padding: int = 3,
    max_attempts: int = 64,
) -> Path:
    """Atomically reserve the next ``v###`` slot by creating an empty file.

    The host adapter is expected to overwrite the returned path with the real
    save (``cmds.file(rename=...)`` then ``cmds.file(save=True, ...)`` for
    Maya; ``app.project.save(File(...))`` for AE).

    Args:
        folder: Target directory. Created if missing.
        prefix: Asset or shot name (filename prefix).
        task: Task slug.
        variant: Already-normalised variant slug.
        ext: Extension without leading dot.
        padding: Width of the zero-padded version number.
        max_attempts: Safety bound to avoid pathological loops if many slots
            are being grabbed simultaneously.

    Returns:
        The reserved file path (currently zero-bytes on disk).

    Raises:
        VersionReservationError: If we couldn't claim a slot after
            ``max_attempts``.
    """
    folder.mkdir(parents=True, exist_ok=True)

    candidate_version = next_version(folder, prefix, task, variant, ext)
    for _ in range(max_attempts):
        filename = f"{prefix}_{task}_{variant}_v{candidate_version:0{padding}d}.{ext}"
        target = folder / filename
        try:
            # Exclusive create succeeds for exactly one caller; everyone else
            # races to the next candidate.
            with target.open("xb"):
                pass
            return target
        except FileExistsError:
            candidate_version += 1
            continue

    raise VersionReservationError(
        f"Could not reserve a version slot under {folder} after "
        f"{max_attempts} attempts; another artist may be publishing rapidly."
    )

"""Publish version folder scanning and reservation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .paths import version_dir_name


@dataclass(frozen=True)
class PublishEntry:
    """One version folder under publish/<type>/."""

    path: Path
    asset: str
    publish_type: str
    variant: str
    version: int

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def summary(self) -> str:
        if not self.path.is_dir():
            return "—"
        try:
            count = sum(1 for c in self.path.iterdir() if c.is_file())
            subdirs = sum(1 for c in self.path.iterdir() if c.is_dir())
            parts = []
            if count:
                parts.append(f"{count} file(s)")
            if subdirs:
                parts.append(f"{subdirs} folder(s)")
            return ", ".join(parts) if parts else "empty"
        except OSError:
            return "—"

    @property
    def modified(self) -> str:
        try:
            mtime = self.path.stat().st_mtime
            return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        except OSError:
            return "—"


def _dir_regex(
    asset: str, publish_type: str, variant: Optional[str], padding: int
) -> re.Pattern[str]:
    variant_pattern = r"(?P<variant>[a-z0-9][a-z0-9_-]*)" if variant is None else re.escape(variant)
    return re.compile(
        rf"^{re.escape(asset)}_{re.escape(publish_type)}_{variant_pattern}_v(?P<version>\d+)$",
        re.IGNORECASE,
    )


def list_publish_versions(
    folder: Path,
    asset: str,
    publish_type: str,
    *,
    variant: Optional[str] = None,
    padding: int = 3,
) -> List[PublishEntry]:
    if not folder.exists():
        return []
    pattern = _dir_regex(asset, publish_type, variant, padding)
    entries: List[PublishEntry] = []
    for child in folder.iterdir():
        if not child.is_dir():
            continue
        match = pattern.match(child.name)
        if not match:
            continue
        this_variant = match.group("variant") if variant is None else variant
        entries.append(
            PublishEntry(
                path=child,
                asset=asset,
                publish_type=publish_type,
                variant=this_variant,
                version=int(match.group("version")),
            )
        )
    entries.sort(key=lambda e: (e.variant, e.version), reverse=True)
    return entries


def next_version(
    folder: Path,
    asset: str,
    publish_type: str,
    variant: str,
    *,
    padding: int = 3,
) -> int:
    existing = list_publish_versions(
        folder, asset, publish_type, variant=variant, padding=padding
    )
    if not existing:
        return 1
    return max(e.version for e in existing) + 1


class VersionReservationError(RuntimeError):
    pass


def reserve_version_dir(
    folder: Path,
    asset: str,
    publish_type: str,
    variant: str,
    *,
    padding: int = 3,
    max_attempts: int = 64,
) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    candidate = next_version(folder, asset, publish_type, variant, padding=padding)
    for _ in range(max_attempts):
        name = version_dir_name(asset, publish_type, variant, candidate, padding=padding)
        target = folder / name
        try:
            target.mkdir()
            return target
        except FileExistsError:
            candidate += 1
    raise VersionReservationError(
        f"Could not reserve version folder under {folder} after {max_attempts} attempts."
    )

"""Asset discovery on the show drive (filtered categories)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from .context import StudioContext
from .schema import AssetPublishSchema


def _list_subdirs(folder: Path) -> List[str]:
    if not folder.exists():
        return []
    try:
        return sorted(
            (entry.name for entry in folder.iterdir() if entry.is_dir()),
            key=str.lower,
        )
    except PermissionError:
        return []


@dataclass
class AssetDiscovery:
    """Scan ``assets/<category>/<asset>/`` with caching and category whitelist."""

    context: StudioContext
    schema: AssetPublishSchema
    _categories_on_disk: List[str] = field(default_factory=list, init=False, repr=False)
    _assets: Dict[str, List[str]] = field(default_factory=dict, init=False, repr=False)
    _loaded: bool = field(default=False, init=False, repr=False)

    def invalidate(self) -> None:
        self._categories_on_disk = []
        self._assets = {}
        self._loaded = False

    def categories(self) -> List[str]:
        self._ensure_loaded()
        disk_lower = {c.lower(): c for c in self._categories_on_disk}
        result: List[str] = []
        for cat in self.schema.allowed_categories:
            if cat.lower() in disk_lower:
                result.append(disk_lower[cat.lower()])
        return result

    def assets(self, category: str) -> List[str]:
        self._ensure_loaded()
        if category in self._assets:
            return list(self._assets[category])
        names = _list_subdirs(self.context.assets_root / category)
        self._assets[category] = names
        return list(names)

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._categories_on_disk = _list_subdirs(self.context.assets_root)
        allowed = {c.lower() for c in self.schema.allowed_categories}
        for category in self._categories_on_disk:
            if category.lower() in allowed:
                self._assets[category] = _list_subdirs(
                    self.context.assets_root / category
                )
        self._loaded = True

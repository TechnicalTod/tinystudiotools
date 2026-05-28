"""Show-drive discovery: categories, assets, episodes, sequences, shots.

Network paths can be slow, so each ``ShowDiscovery`` instance caches the
results it sees during a UI session. Call :meth:`ShowDiscovery.invalidate`
to force a re-scan.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from .context import StudioContext


def _list_subdirs(folder: Path) -> List[str]:
    """Return immediate sub-directory names (sorted, case-insensitive)."""
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
class ShowDiscovery:
    """Show-drive scanner with a per-instance cache.

    Use one instance per publisher session; the UI calls :meth:`invalidate`
    when the artist hits *Refresh*.
    """

    context: StudioContext
    _asset_categories: List[str] = field(default_factory=list, init=False, repr=False)
    _assets: Dict[str, List[str]] = field(default_factory=dict, init=False, repr=False)
    _episodes: List[str] = field(default_factory=list, init=False, repr=False)
    _sequences: Dict[str, List[str]] = field(default_factory=dict, init=False, repr=False)
    _shots: Dict[str, List[str]] = field(default_factory=dict, init=False, repr=False)
    _loaded: bool = field(default=False, init=False, repr=False)

    # --- public API -------------------------------------------------------
    def invalidate(self) -> None:
        """Drop the cache so the next call re-scans the show drive."""
        self._asset_categories = []
        self._assets = {}
        self._episodes = []
        self._sequences = {}
        self._shots = {}
        self._loaded = False

    def asset_categories(self) -> List[str]:
        self._ensure_loaded()
        return list(self._asset_categories)

    def assets(self, category: str) -> List[str]:
        self._ensure_loaded()
        if category in self._assets:
            return list(self._assets[category])
        # Lazy: category exists on disk but we haven't visited it yet.
        names = _list_subdirs(self.context.assets_root / category)
        self._assets[category] = names
        return list(names)

    def episodes(self) -> List[str]:
        self._ensure_loaded()
        return list(self._episodes)

    def sequences(self, episode: str) -> List[str]:
        self._ensure_loaded()
        if episode in self._sequences:
            return list(self._sequences[episode])
        names = _list_subdirs(self.context.episodes_root / episode)
        self._sequences[episode] = names
        return list(names)

    def shots(self, episode: str, sequence: str) -> List[str]:
        self._ensure_loaded()
        key = f"{episode}/{sequence}"
        if key in self._shots:
            return list(self._shots[key])
        names = _list_subdirs(self.context.episodes_root / episode / sequence)
        self._shots[key] = names
        return list(names)

    # --- internals --------------------------------------------------------
    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._asset_categories = _list_subdirs(self.context.assets_root)
        for category in self._asset_categories:
            self._assets[category] = _list_subdirs(self.context.assets_root / category)
        self._episodes = _list_subdirs(self.context.episodes_root)
        for episode in self._episodes:
            self._sequences[episode] = _list_subdirs(self.context.episodes_root / episode)
            for sequence in self._sequences[episode]:
                key = f"{episode}/{sequence}"
                self._shots[key] = _list_subdirs(
                    self.context.episodes_root / episode / sequence
                )
        self._loaded = True

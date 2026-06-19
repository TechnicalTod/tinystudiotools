"""Shared types for Unreal asset import."""

from __future__ import annotations

from typing import Callable, Dict, FrozenSet, List, NamedTuple, Optional

WarnFn = Callable[[str], None]


class StaticMeshTextureImportResult(NamedTuple):
    imported_textures: Optional[List[str]]
    orma_channels_by_slot: Dict[str, FrozenSet[str]]
    scalar_values_by_slot: Dict[str, Dict[str, object]]

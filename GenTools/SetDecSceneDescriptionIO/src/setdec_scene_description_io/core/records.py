"""The adapter <-> core interchange record.

An :class:`AssetRecord` is the single currency passed in both directions:

* **Export** - an adapter gathers the live scene into records, then
  :func:`setdec_scene_description_io.core.usd_io.write_usd` serialises them.
* **Import** - :func:`setdec_scene_description_io.core.usd_io.parse_usd` reads a
  ``.usda`` into records, then an adapter rebuilds the scene from them.

``transform`` carries a USD-space local matrix (a ``pxr.Gf.Matrix4d``). It is
typed ``Any`` so this module never has to import ``pxr``; the adapters and the
USD layer that produce / consume it do.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class AssetRecord:
    """One prim's worth of scene data.

    Attributes:
        hierarchy_path: Slash-delimited prim path (e.g. ``/ENV/wall/crate``).
        transform: USD-space local transform (``pxr.Gf.Matrix4d``), or ``None``.
        asset_name: Published asset short name (``None`` for plain groups).
        base_path: Published asset base path (``None`` for plain groups).
        version: Published asset version (e.g. ``v003``).
        variant: Published asset variant (e.g. ``base``).
    """

    hierarchy_path: str
    transform: Any = None
    asset_name: Optional[str] = None
    base_path: Optional[str] = None
    version: Optional[str] = None
    variant: Optional[str] = None

    @property
    def is_group(self) -> bool:
        """True when the record is a plain transform group (no referenced asset)."""
        return not (self.base_path and str(self.base_path).strip())

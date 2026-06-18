"""Import published custom geo static meshes into the shot level sequence."""

from __future__ import annotations

from .custom_geo_ops import import_custom_animated_geometry_items
from .manifest import CustomAnimatedGeometryItem
from .setup_ops import ShotSetupResult


def import_custom_geo_items(
    setup: ShotSetupResult,
    items: list[CustomAnimatedGeometryItem],
) -> None:
    import_custom_animated_geometry_items(setup, items)

"""Dispatch custom animated geometry import by product type."""

from __future__ import annotations

import os
from typing import Callable

import unreal

from . import alembic_ops, animated_fbx_ops, setdec_shot_ops
from .manifest import (
    PRODUCT_TYPE_ALEMBIC,
    PRODUCT_TYPE_ANIMATED_FBX,
    PRODUCT_TYPE_SETDEC_ANIMATED,
    CustomAnimatedGeometryItem,
)
from .setup_ops import ShotSetupResult

WarnFn = Callable[[str], None]


def _warn_default(message: str) -> None:
    print(message)


def _filter_importable_items(
    items: list[CustomAnimatedGeometryItem],
    *,
    warn: WarnFn,
) -> list[CustomAnimatedGeometryItem]:
    importable: list[CustomAnimatedGeometryItem] = []
    for item in items:
        if item.publish_status == "failed":
            warn("Skipping failed publish item '{}': {}".format(item.name, item.error))
            continue
        if not item.export_path:
            warn("Skipping '{}' because exportPath is missing.".format(item.name))
            continue
        if not os.path.isfile(item.export_path):
            warn(
                "Skipping '{}' because export file was not found: {}".format(
                    item.name,
                    item.export_path,
                )
            )
            continue
        importable.append(item)
    return importable


def import_custom_animated_geometry_items(
    setup: ShotSetupResult,
    items: list[CustomAnimatedGeometryItem],
    *,
    warn: WarnFn = _warn_default,
) -> list[str]:
    importable = _filter_importable_items(items, warn=warn)
    if not importable:
        return []

    saved_assets: list[str] = []
    animated_fbx_items = [
        item
        for item in importable
        if item.product_type == PRODUCT_TYPE_ANIMATED_FBX
    ]
    alembic_items = [
        item for item in importable if item.product_type == PRODUCT_TYPE_ALEMBIC
    ]
    setdec_items = [
        item
        for item in importable
        if item.product_type == PRODUCT_TYPE_SETDEC_ANIMATED
    ]

    if animated_fbx_items:
        saved_assets.extend(
            animated_fbx_ops.import_animated_fbx_items(setup, animated_fbx_items)
        )
    if alembic_items:
        saved_assets.extend(alembic_ops.import_alembic_items(setup, alembic_items))
    if setdec_items:
        saved_assets.extend(
            setdec_shot_ops.import_setdec_items(setup, setdec_items, warn=warn)
        )

    for asset_path in saved_assets:
        unreal.EditorAssetLibrary.save_asset(asset_path)

    return saved_assets

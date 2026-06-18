"""Pure helpers for custom animated geometry classification."""

from __future__ import annotations

from typing import Any

from .constants import (
    CUSTOM_GEO_ALEMBIC_SET_NAME,
    CUSTOM_GEO_FBX_SET_NAME,
    EXPORT_FORMAT_ALEMBIC,
    EXPORT_FORMAT_FBX,
    PRODUCT_TYPE_ALEMBIC,
    PRODUCT_TYPE_ANIMATED_FBX,
    PRODUCT_TYPE_SETDEC_ANIMATED,
)


def export_format_for_source_set(source_set: str) -> str:
    if source_set == CUSTOM_GEO_ALEMBIC_SET_NAME:
        return EXPORT_FORMAT_ALEMBIC
    return EXPORT_FORMAT_FBX


def product_type_for_item(*, export_format: str, is_set_dec: bool) -> str:
    if is_set_dec:
        return PRODUCT_TYPE_SETDEC_ANIMATED
    if export_format == EXPORT_FORMAT_ALEMBIC:
        return PRODUCT_TYPE_ALEMBIC
    return PRODUCT_TYPE_ANIMATED_FBX


def is_published_setdec_from_attrs(attrs: dict[str, Any]) -> bool:
    if not attrs.get("published"):
        return False
    required = ("assetName", "basePath", "variantName", "version")
    return all(str(attrs.get(key) or "").strip() for key in required)


def partial_setdec_warning(attrs: dict[str, Any]) -> str | None:
    if not attrs.get("published"):
        return None
    if is_published_setdec_from_attrs(attrs):
        return None
    return (
        "Published Set Dec attrs are incomplete on '{}'; treating as custom geo.".format(
            attrs.get("name", "unknown")
        )
    )


def item_key(source_set: str, member_name: str) -> str:
    return "{}|{}".format(source_set, member_name)

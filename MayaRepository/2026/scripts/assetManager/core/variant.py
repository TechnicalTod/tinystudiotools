"""Variant name normalisation."""

from __future__ import annotations

import re
from typing import Optional

from .schema import AssetPublishSchema

_VARIANT_ALLOWED = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def normalize_variant(value: Optional[str], schema: AssetPublishSchema) -> str:
    if value is None or not value.strip():
        return schema.default_variant
    cleaned = value.strip().lower().replace(" ", "_")
    if not _VARIANT_ALLOWED.match(cleaned):
        raise ValueError(
            f"Invalid variant {value!r}. Use lowercase letters, digits, underscores, dashes."
        )
    return cleaned

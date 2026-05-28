"""Asset folder name normalisation."""

from __future__ import annotations

import re
from typing import Optional

_ASSET_ALLOWED = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


def normalize_asset_name(value: Optional[str]) -> str:
    """Normalise a show-drive asset folder name.

    Spaces become underscores; the result must be alphanumeric with optional
    underscores and dashes (``Prop02``, ``Hero_Chair``).
    """
    if value is None or not value.strip():
        raise ValueError("Asset name is required.")
    cleaned = value.strip().replace(" ", "_")
    if not _ASSET_ALLOWED.match(cleaned):
        raise ValueError(
            f"Invalid asset name {value!r}. "
            "Use letters, digits, underscores, and dashes; must start with a letter or digit."
        )
    return cleaned

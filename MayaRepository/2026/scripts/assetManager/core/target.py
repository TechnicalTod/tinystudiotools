"""Publish target descriptor."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AssetPublishTarget:
    """One publish destination on the show drive."""

    category: str
    asset: str
    publish_type: str
    variant: str
    dcc: str = "maya"

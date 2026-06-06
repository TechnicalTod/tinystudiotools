"""Standalone (dev) adapter for iterating on the UI outside a DCC."""

from __future__ import annotations

import logging
from typing import List

from ..core.records import AssetRecord
from .base import SceneAdapter

logger = logging.getLogger(__name__)


class StandaloneAdapter(SceneAdapter):
    """No-op adapter that logs instead of touching a scene."""

    name = "standalone"
    label = "Standalone"

    def gather(self) -> List[AssetRecord]:
        logger.info("StandaloneAdapter.gather() - no live scene; returning [].")
        return []

    def apply(self, records: List[AssetRecord]) -> None:
        logger.info("StandaloneAdapter.apply() - %d record(s) ignored.", len(records))

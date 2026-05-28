"""Standalone (dev) adapter.

Useful for iterating on the UI outside Maya / AE: every action is logged to
stdout and the publisher gets a fake "scene path" via a member variable.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from .base import HostAdapter

logger = logging.getLogger(__name__)


class StandaloneAdapter(HostAdapter):
    """No-op adapter that mostly just logs."""

    name = "standalone"
    label = "Standalone"

    def __init__(self) -> None:
        self._fake_scene: Optional[Path] = None
        self._dirty = False

    # ---- queries --------------------------------------------------------
    def current_scene_path(self) -> Optional[Path]:
        return self._fake_scene

    def is_modified(self) -> bool:
        return self._dirty

    # ---- actions --------------------------------------------------------
    def save_as(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Replace any reserved placeholder with a tiny marker payload so it's
        # obvious the standalone path was exercised.
        path.write_text("# tinystudio workfile publisher (standalone) placeholder\n", encoding="utf-8")
        self._fake_scene = path
        self._dirty = False
        logger.info("StandaloneAdapter wrote %s", path)

    def open(self, path: Path) -> None:
        self._fake_scene = path
        self._dirty = False
        logger.info("StandaloneAdapter opened %s", path)

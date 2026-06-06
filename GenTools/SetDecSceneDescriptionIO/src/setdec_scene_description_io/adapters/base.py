"""Scene adapter contract.

The core never talks to a DCC directly. Each adapter implements two verbs:

* :py:meth:`SceneAdapter.gather` - read the live scene into records (export).
* :py:meth:`SceneAdapter.apply`  - rebuild the scene from records (import).

This keeps Maya, Unreal and dev-standalone code paths swappable.
"""

from __future__ import annotations

import abc
from typing import List

from ..core.records import AssetRecord


class SceneAdapterError(RuntimeError):
    """Raised when the host refuses or fails to gather / apply a scene."""


class SceneAdapter(abc.ABC):
    """Abstract base class for DCC-specific scene IO."""

    #: Short host identifier (``"maya"`` / ``"unreal"`` / ``"standalone"``).
    name: str = "base"

    #: Human-readable label for window titles / status text.
    label: str = "Host"

    @abc.abstractmethod
    def gather(self) -> List[AssetRecord]:
        """Collect the current scene's ``ENV`` hierarchy into records."""

    @abc.abstractmethod
    def apply(self, records: List[AssetRecord]) -> None:
        """Rebuild the scene hierarchy from records."""

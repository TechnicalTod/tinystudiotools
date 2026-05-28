"""Host adapter contract.

The publisher core never talks to a DCC directly. It calls into a
:class:`HostAdapter` for the three host-specific verbs:

* :py:meth:`HostAdapter.current_scene_path` - what's open right now?
* :py:meth:`HostAdapter.save_as`            - write the current scene to disk.
* :py:meth:`HostAdapter.open`               - load a scene from disk.

This keeps Maya, AE and dev-standalone code paths swappable.
"""

from __future__ import annotations

import abc
from pathlib import Path
from typing import Optional


class HostAdapterError(RuntimeError):
    """Raised when the host refuses or fails to perform an operation."""


class HostAdapter(abc.ABC):
    """Abstract base class for DCC-specific actions."""

    #: Short host identifier (``"maya"`` or ``"standalone"`` for this Python package).
    name: str = "base"

    #: Human-readable label for status text.
    label: str = "Host"

    # ---- queries --------------------------------------------------------
    @abc.abstractmethod
    def current_scene_path(self) -> Optional[Path]:
        """Return the path of the currently open scene, or ``None``."""

    def is_modified(self) -> bool:
        """Whether the current scene has unsaved changes.

        Default implementation returns ``False`` so adapters without a cheap
        modified-state check can opt out. Overridden by Maya / AE adapters.
        """
        return False

    # ---- actions --------------------------------------------------------
    @abc.abstractmethod
    def save_as(self, path: Path) -> None:
        """Save the current scene to ``path``.

        The target file may already exist as a zero-byte placeholder (the
        publisher reserves the version slot before calling the adapter); the
        adapter is expected to overwrite it.
        """

    @abc.abstractmethod
    def open(self, path: Path) -> None:
        """Load the scene at ``path`` into the host."""

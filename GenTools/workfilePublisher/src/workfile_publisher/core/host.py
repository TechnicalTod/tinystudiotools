"""Host (DCC) detection.

The publisher runs in two Python modes:

* ``maya`` - inside Autodesk Maya (``maya.cmds`` importable).
* ``standalone`` - dev / debug mode outside any DCC.

After Effects uses the native ScriptUI tool in ``AERepository/tools/WorkfilePublisher.jsx``
(not this Python package).

``detect_host`` is intentionally side-effect free; the actual host adapter is
created by :mod:`workfile_publisher.adapters` based on this string.
"""

from __future__ import annotations

import sys
from typing import Literal, Optional

HostName = Literal["maya", "standalone"]


def _maya_available() -> bool:
    """Return True if ``maya.cmds`` can be imported.

    We only import on demand so importing this module never pulls Maya into
    standalone runs.
    """
    try:
        import maya.cmds  # noqa: F401
    except Exception:
        return False
    return True


def detect_host(cli_host: Optional[str] = None) -> HostName:
    """Resolve which DCC host the publisher is running under.

    Args:
        cli_host: Optional override from the command line (``--host`` flag).
            Wins over auto-detection when set to a known value.

    Returns:
        One of ``"maya"`` or ``"standalone"``.

    Raises:
        ValueError: If ``cli_host`` is provided but is not a known host name.
    """
    if cli_host:
        lowered = cli_host.strip().lower()
        if lowered not in ("maya", "standalone"):
            raise ValueError(
                f"Unknown --host {cli_host!r}; expected maya or standalone."
            )
        return lowered  # type: ignore[return-value]

    if _maya_available():
        return "maya"

    return "standalone"

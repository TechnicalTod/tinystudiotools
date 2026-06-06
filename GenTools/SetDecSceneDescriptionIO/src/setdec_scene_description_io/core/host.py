"""Host (DCC) detection.

The scene-description tool runs in three Python modes:

* ``maya`` - inside Autodesk Maya (``maya.cmds`` importable).
* ``unreal`` - inside Unreal Engine's Python (``unreal`` importable).
* ``standalone`` - dev / debug mode outside any DCC.

``detect_host`` is side-effect free; the matching adapter is created by
:func:`setdec_scene_description_io.adapters.build_adapter`.
"""

from __future__ import annotations

from typing import Literal, Optional

HostName = Literal["maya", "unreal", "standalone"]

_KNOWN_HOSTS = ("maya", "unreal", "standalone")


def _maya_available() -> bool:
    try:
        import maya.cmds  # noqa: F401
    except Exception:
        return False
    return True


def _unreal_available() -> bool:
    try:
        import unreal  # noqa: F401
    except Exception:
        return False
    return True


def detect_host(cli_host: Optional[str] = None) -> HostName:
    """Resolve which DCC host the tool is running under.

    Args:
        cli_host: Optional override; wins over auto-detection when it names a
            known host.

    Raises:
        ValueError: If ``cli_host`` is provided but unknown.
    """
    if cli_host:
        lowered = cli_host.strip().lower()
        if lowered not in _KNOWN_HOSTS:
            raise ValueError(
                f"Unknown host {cli_host!r}; expected one of {_KNOWN_HOSTS}."
            )
        return lowered  # type: ignore[return-value]

    if _maya_available():
        return "maya"
    if _unreal_available():
        return "unreal"
    return "standalone"

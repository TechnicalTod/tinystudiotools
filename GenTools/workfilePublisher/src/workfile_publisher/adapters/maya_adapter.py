"""Maya host adapter.

Imports of ``maya.cmds`` happen lazily so this module is importable even when
the publisher is launched standalone (the AE / dev path never instantiates a
:class:`MayaAdapter`).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .base import HostAdapter, HostAdapterError


class MayaAdapter(HostAdapter):
    """Talk to the Maya scene via ``maya.cmds.file``."""

    name = "maya"
    label = "Maya"

    def __init__(self) -> None:
        try:
            import maya.cmds  # noqa: F401
        except Exception as exc:  # pragma: no cover - only runs inside Maya
            raise HostAdapterError(
                "MayaAdapter requires running inside Autodesk Maya."
            ) from exc

    # ---- queries --------------------------------------------------------
    def current_scene_path(self) -> Optional[Path]:
        import maya.cmds as cmds

        scene = cmds.file(query=True, sceneName=True)
        if not scene:
            return None
        return Path(scene)

    def is_modified(self) -> bool:
        import maya.cmds as cmds

        try:
            return bool(cmds.file(query=True, modified=True))
        except Exception:
            return False

    # ---- actions --------------------------------------------------------
    def save_as(self, path: Path) -> None:
        import maya.cmds as cmds

        path.parent.mkdir(parents=True, exist_ok=True)

        suffix = path.suffix.lower()
        if suffix == ".ma":
            maya_type = "mayaAscii"
        elif suffix == ".mb":
            maya_type = "mayaBinary"
        else:
            raise HostAdapterError(
                f"MayaAdapter cannot save extension {suffix!r}; expected .ma or .mb."
            )

        # If the publisher pre-reserved an empty placeholder, drop it so Maya
        # doesn't refuse the rename / overwrite.
        if path.exists() and path.stat().st_size == 0:
            try:
                path.unlink()
            except OSError:
                pass

        try:
            cmds.file(rename=str(path))
            cmds.file(save=True, type=maya_type)
        except Exception as exc:
            raise HostAdapterError(f"Maya save_as failed: {exc}") from exc

    def open(self, path: Path) -> None:
        import maya.cmds as cmds

        try:
            cmds.file(str(path), open=True, force=True, ignoreVersion=True)
        except Exception as exc:
            raise HostAdapterError(f"Maya open failed: {exc}") from exc

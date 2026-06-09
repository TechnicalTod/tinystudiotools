"""Maya scene API used by the workfile manager.

All ``maya.cmds`` / ``maya.mel`` imports live here so core and UI modules
stay importable outside Maya where useful.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional


class MayaHostError(RuntimeError):
    """Raised when Maya refuses or fails to perform an operation."""


class MayaHost:
    """Talk to the Maya scene via ``maya.cmds.file``."""

    name = "maya"
    label = "Maya"

    def __init__(self) -> None:
        try:
            import maya.cmds  # noqa: F401
        except Exception as exc:  # pragma: no cover - only runs inside Maya
            raise MayaHostError(
                "MayaHost requires running inside Autodesk Maya."
            ) from exc

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

    def _set_project(self, project_dir: Path) -> None:
        import maya.mel as mel

        project_dir.mkdir(parents=True, exist_ok=True)
        path_str = str(project_dir).replace("\\", "/")
        try:
            mel.eval(f'setProject "{path_str}"')
        except Exception as exc:
            raise MayaHostError(
                f"Maya set project failed for {project_dir}: {exc}"
            ) from exc

    def save_as(self, path: Path) -> None:
        import maya.cmds as cmds

        self._set_project(path.parent)

        suffix = path.suffix.lower()
        if suffix == ".ma":
            maya_type = "mayaAscii"
        elif suffix == ".mb":
            maya_type = "mayaBinary"
        else:
            raise MayaHostError(
                f"MayaHost cannot save extension {suffix!r}; expected .ma or .mb."
            )

        if path.exists() and path.stat().st_size == 0:
            try:
                path.unlink()
            except OSError:
                pass

        try:
            cmds.file(rename=str(path))
            cmds.file(save=True, type=maya_type)
        except Exception as exc:
            raise MayaHostError(f"Maya save_as failed: {exc}") from exc

    def open(self, path: Path) -> None:
        import maya.cmds as cmds

        self._set_project(path.parent)

        try:
            cmds.file(str(path), open=True, force=True, ignoreVersion=True)
        except Exception as exc:
            raise MayaHostError(f"Maya open failed: {exc}") from exc

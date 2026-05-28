"""Maya scene API for Playblast Manager.

Single place where ``maya.cmds`` is imported.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


_DEFAULT_CAMERAS = frozenset({"front", "side", "top", "persp"})


@dataclass(frozen=True)
class CameraInfo:
    """One renderable camera in the scene."""

    shape: str
    transform: str
    width: int
    height: int
    renderable: bool


class MayaHost:
    """Concrete Maya scene API."""

    name = "maya"
    label = "Maya"

    def current_scene_path(self) -> Optional[Path]:
        import maya.cmds as cmds

        raw = cmds.file(query=True, sceneName=True) or ""
        if not raw:
            return None
        return Path(str(raw).replace("\\", "/"))

    def is_modified(self) -> bool:
        import maya.cmds as cmds

        return bool(cmds.file(query=True, modified=True))

    def scene_basename(self) -> str:
        path = self.current_scene_path()
        return path.stem if path else "untitled"

    def playback_range(self) -> Tuple[float, float]:
        import maya.cmds as cmds

        start = float(cmds.playbackOptions(minTime=True, query=True))
        end = float(cmds.playbackOptions(maxTime=True, query=True))
        return start, end

    def save_scene(self) -> bool:
        """Save the current scene (prompts if needed). Returns True on success."""
        import maya.cmds as cmds

        path = self.current_scene_path()
        if path is None:
            return False
        try:
            suffix = path.suffix.lower()
            file_type = "mayaBinary" if suffix == ".mb" else "mayaAscii"
            cmds.file(save=True, type=file_type)
            return True
        except Exception:
            return False

    def list_renderable_cameras(self) -> List[CameraInfo]:
        import maya.cmds as cmds

        cameras: list[CameraInfo] = []
        for shape in cmds.ls(type="camera") or []:
            short = shape.split("|")[-1]
            if short in _DEFAULT_CAMERAS:
                continue
            parent = (cmds.listRelatives(shape, parent=True, fullPath=False) or [shape])[0]
            renderable = bool(cmds.getAttr(f"{shape}.renderable"))
            width, height = self._camera_resolution(shape)
            cameras.append(
                CameraInfo(
                    shape=short,
                    transform=parent.split("|")[-1],
                    width=width,
                    height=height,
                    renderable=renderable,
                )
            )

        cameras.sort(key=lambda c: c.shape.lower())
        return cameras

    def _camera_resolution(self, camera_shape: str) -> Tuple[int, int]:
        import maya.cmds as cmds

        for node in cmds.listConnections(camera_shape, type="resolution") or []:
            try:
                return int(cmds.getAttr(f"{node}.width")), int(cmds.getAttr(f"{node}.height"))
            except Exception:
                pass

        for attr_w, attr_h in (
            ("renderResolutionWidth", "renderResolutionHeight"),
            ("imageWidth", "imageHeight"),
        ):
            if cmds.attributeQuery(attr_w, node=camera_shape, exists=True):
                try:
                    return int(cmds.getAttr(f"{camera_shape}.{attr_w}")), int(
                        cmds.getAttr(f"{camera_shape}.{attr_h}")
                    )
                except Exception:
                    pass

        width = int(cmds.getAttr("defaultResolution.width"))
        height = int(cmds.getAttr("defaultResolution.height"))
        ratio = float(cmds.getAttr("defaultResolution.deviceAspectRatio"))
        if ratio:
            height = int(round(width / ratio))
        return width, height

    def _active_model_panel(self) -> Optional[str]:
        import maya.cmds as cmds

        panel = cmds.getPanel(withFocus=True)
        if panel and "modelPanel" in panel:
            return panel
        for candidate in cmds.getPanel(type="modelPanel") or []:
            return candidate
        return None

    def playblast(
        self,
        camera: str,
        output_dir: Path,
        filename_base: str,
        start_frame: float,
        end_frame: float,
        width: int,
        height: int,
        *,
        show_ornaments: bool,
        display_mode: str,
        quality: int,
        frame_padding: int = 4,
    ) -> List[Path]:
        """Render a PNG sequence through ``camera`` into ``output_dir``."""
        import maya.cmds as cmds

        if not cmds.objExists(camera):
            raise RuntimeError(f"Camera does not exist: {camera}")

        output_dir.mkdir(parents=True, exist_ok=True)
        prefix = str((output_dir / f"{filename_base}.{'#' * frame_padding}").as_posix())

        panel = self._active_model_panel()
        previous_camera = None
        previous_display = None
        if panel:
            previous_camera = cmds.modelPanel(panel, query=True, camera=True)
            try:
                previous_display = cmds.modelEditor(panel, query=True, displayAppearance=True)
            except Exception:
                previous_display = None
            cmds.lookThru(panel, camera)
            try:
                cmds.modelEditor(panel, edit=True, displayAppearance=display_mode)
            except Exception:
                pass

        try:
            cmds.playblast(
                compression="png",
                format="image",
                percent=100,
                quality=quality,
                viewer=False,
                startTime=start_frame,
                endTime=end_frame,
                offScreen=True,
                forceOverwrite=True,
                filename=prefix,
                widthHeight=[width, height],
                showOrnaments=show_ornaments,
            )
        finally:
            if panel and previous_camera:
                try:
                    cmds.lookThru(panel, previous_camera)
                except Exception:
                    pass
            if panel and previous_display:
                try:
                    cmds.modelEditor(panel, edit=True, displayAppearance=previous_display)
                except Exception:
                    pass

        pattern = f"{filename_base}.*.png"
        frames = sorted(output_dir.glob(pattern))
        if not frames:
            frames = sorted(output_dir.glob("*.png"))
        return frames
